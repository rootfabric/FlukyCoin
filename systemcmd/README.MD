# Активировать службы
sudo systemctl enable node.service
sudo systemctl enable explorer.service

# Запустить службы
sudo systemctl start node.service
sudo systemctl start explorer.service


# Проверка статуса node.service
sudo systemctl status node.service

# Проверка статуса explorer.service
sudo systemctl status explorer.service



# Шаг 1: Создание файла службы для node.service
sudo tee /etc/systemd/system/node.service > /dev/null <<EOF
[Unit]
Description=Node Service
After=network.target

[Service]
User=root
WorkingDirectory=/root/F
ExecStart=/usr/bin/python3 /root/F/main.py --config node_config_server_fvds.yaml
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Шаг 2: Создание файла службы для explorer.service
sudo tee /etc/systemd/system/explorer.service > /dev/null <<EOF
[Unit]
Description=Explorer Web Service
After=network.target

[Service]
User=root
WorkingDirectory=/root/F/explorer
ExecStart=/usr/bin/python3 /root/F/explorer/explorer_web.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Шаг 3: Активировать и запустить службы
sudo systemctl enable node.service
sudo systemctl enable explorer.service

sudo systemctl start node.service
sudo systemctl start explorer.service

# Шаг 4: Проверка статуса служб
sudo systemctl status node.service
sudo systemctl status explorer.service
