import main
import os

install_location = "/home/akatsukialt/production/source/main.py"
work_directory = "/home/akatsukialt/data"
secrets_path = "/home/akatsukialt/secrets.json"
user = "akatsukialt"
service_install_location = "/etc/systemd/system/"
BASE_SERVICE = f"""
[Unit]
Description=(DESCRIPTION)
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User={user}
WorkingDirectory={work_directory}
ExecStart=/usr/bin/env python3 {install_location} (FUNCTION) {secrets_path}

[Install]
WantedBy=multi-user.target"""

if __name__ == "__main__":
    svc_prefix = "akatalt-"
    base_script = "#!/bin/bash\n"
    enable_script = base_script
    disable_script = base_script
    install_script = f"{base_script}mv *.service {service_install_location}"
    os.makedirs("data/systemd/", exist_ok=True)
    for fn in main.function_list:
        enable_script += f"systemctl enable --now {svc_prefix}{fn.__name__}\n"
        disable_script += f"systemctl disable --now {svc_prefix}{fn.__name__}\n"
        string = BASE_SERVICE.replace("(FUNCTION)", fn.__name__).replace(
            "(DESCRIPTION)", f"Akatsuki! Alt {fn.__name__} service")
        with open(f"data/systemd/{svc_prefix}{fn.__name__}.service", "w") as f:
            f.write(string)
        with open(f"data/systemd/enable.sh", "w") as f:
            f.write(enable_script)
        with open(f"data/systemd/disable.sh", "w") as f:
            f.write(disable_script)
        with open(f"data/systemd/install.sh", "w") as f:
            f.write(install_script)