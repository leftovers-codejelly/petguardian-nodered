PET GUARDIAN
README / Developer Setup Guide

Project: CodeJelly 2026 - Pet Guardian
Platform: Raspberry Pi 5 / Raspberry Pi OS
Purpose: Local pet monitoring dashboard using Node-RED, camera streaming,
BLE proximity, environmental sensing, SQLite persistence, and AI pet detection.

===============================================================================
1. OVERVIEW
===============================================================================

Pet Guardian is a Raspberry Pi-based pet monitoring prototype that combines:

- Live camera streaming
- Cat/dog object detection
- BLE pet-tag proximity tracking
- Temperature and humidity monitoring
- SQLite persistence for pet sighting information
- Node-RED Dashboard 2.0 for the user interface

Typical runtime flow:

Camera
  -> Camera Server
  -> MJPEG Stream
  -> OpenCV
  -> MobileNet-SSD
  -> Pet Detection JSON
  -> Node-RED
  -> Dashboard

BLE Beacon
  -> Raspberry Pi Bluetooth
  -> Bleak Python Scanner
  -> JSON
  -> Node-RED
  -> Proximity Status

BME280
  -> I2C
  -> Node-RED
  -> Temperature/Humidity
  -> Dashboard

Pet Detection
  -> SQLite
  -> Last Seen persistence


===============================================================================
2. TESTED REFERENCE HARDWARE
===============================================================================

Original prototype:

- Raspberry Pi 5, 4 GB
- Raspberry Pi Camera Module 3 Wide NoIR
- Adafruit BME280 temperature/humidity/pressure sensor
- Blue Charm BC04P BLE beacon
- Raspberry Pi OS
- Local Wi-Fi network

IMPORTANT:
Different developers may use different camera models. The supplied camera
server is a reference implementation for Picamera2-compatible Raspberry Pi
CSI cameras. USB cameras or other CSI cameras may require changes to the
camera server code.


===============================================================================
3. RECOMMENDED REPOSITORY STRUCTURE
===============================================================================

pet-guardian/
|
|-- README.txt
|
|-- node-red/
|   |-- pet-environment.json
|   |-- ble-tracker.json
|   |-- camera.json
|   |-- pet-detection.json
|   `-- pet-database.json
|
|-- camera/
|   `-- petguardian_camera.py
|
|-- ble/
|   |-- petguardian_ble_nodered.py
|   `-- petguardian_ble_scan.py
|
|-- ai/
|   |-- pet_detect_nodered.py
|   `-- pet_detect.py
|
|-- systemd/
|   `-- petguardian-camera.service
|
`-- docs/
    `-- optional additional documentation


===============================================================================
4. BASE RASPBERRY PI SETUP
===============================================================================

Update the Pi:

    sudo apt update
    sudo apt upgrade -y

Install base packages:

    sudo apt install -y build-essential git curl python3-venv

Check Python:

    python3 --version

Check your Linux username and home directory:

    whoami
    echo $HOME

Throughout this document, replace:

    <USER>

with your actual Linux username.

Example:

    /home/<USER>

might become:

    /home/broketoof


===============================================================================
5. INSTALL NODE-RED
===============================================================================

Install Node-RED:

    bash <(curl -sL https://github.com/node-red/linux-installers/releases/latest/download/install-update-nodered-deb)

Start Node-RED:

    node-red-start

Enable Node-RED at boot:

    sudo systemctl enable nodered.service

Start the service if needed:

    sudo systemctl start nodered.service

Check status:

    systemctl status nodered.service

Press q to exit the status screen.

Default editor:

    http://<PI-IP>:1880


===============================================================================
6. INSTALL NODE-RED PACKAGES
===============================================================================

Required Node-RED packages:

- Dashboard 2.0
      @flowfuse/node-red-dashboard

- SQLite
      node-red-node-sqlite

- BME280
      node-red-contrib-bme280

Install from:

    Node-RED menu
      -> Manage palette
      -> Install

or:

    cd ~/.node-red

    npm install @flowfuse/node-red-dashboard
    npm install node-red-node-sqlite
    npm install node-red-contrib-bme280

Restart Node-RED if necessary:

    sudo systemctl restart nodered.service


===============================================================================
7. IMPORT THE NODE-RED FLOW TEMPLATES
===============================================================================

Import the supplied JSON files from:

    Node-RED menu
      -> Import

Suggested flow tabs:

- Pet Environment
- BLE Tracker
- Camera
- Pet Detection
- Pet Database

After import, update paths, IP addresses, sensor addresses, and BLE device
names for the local Raspberry Pi.


===============================================================================
8. VALUES THAT MAY NEED TO BE CHANGED AFTER IMPORT
===============================================================================

A. Raspberry Pi IP address

The camera Template node may contain:

    http://192.168.1.115:8000/stream.mjpg

Replace with the developer's Pi IP.

Find the Pi IP with:

    hostname -I


B. Linux username / home directory

Exec nodes may reference:

    /home/<USER>/...

Update them for the current account.


C. BLE beacon

Reference beacon:

    BCPro_217898

If using another beacon, update TARGET_NAME in the BLE scripts.


D. BME280 I2C address

Reference sensor:

    Bus: 1
    Address: 0x77

Some boards use 0x76.

Verify with:

    sudo apt install -y i2c-tools
    sudo i2cdetect -y 1


E. SQLite database path

Reference database:

    /home/<USER>/petguardian.db


===============================================================================
9. CAMERA SETUP
===============================================================================

For a Raspberry Pi CSI camera, power off before connecting/disconnecting it:

    sudo shutdown -h now

After reboot:

    rpicam-hello --list-cameras

Test preview:

    rpicam-hello

Verify Picamera2:

    python3 -c "from picamera2 import Picamera2; print('Picamera2 OK')"

The supplied:

    petguardian_camera.py

is written for a Picamera2-compatible Raspberry Pi camera.

For a USB webcam, a developer may instead use OpenCV VideoCapture, for example:

    cv2.VideoCapture(0)

The important requirement is that the camera server exposes a stream that the
dashboard and AI detector can read.


-------------------------------------------------------------------------------
9.1 DEFAULT CAMERA SERVER
-------------------------------------------------------------------------------

Reference MJPEG server port:

    8000

Example URLs:

    http://<PI-IP>:8000
    http://<PI-IP>:8000/stream.mjpg

Manual test:

    python3 /home/<USER>/pet-guardian/camera/petguardian_camera.py


===============================================================================
10. CAMERA SERVER SYSTEMD SERVICE
===============================================================================

Create:

    /etc/systemd/system/petguardian-camera.service

Example:

[Unit]
Description=Pet Guardian Camera Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<USER>
WorkingDirectory=/home/<USER>/pet-guardian
ExecStart=/usr/bin/python3 /home/<USER>/pet-guardian/camera/petguardian_camera.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target


Reload systemd:

    sudo systemctl daemon-reload

Enable and start:

    sudo systemctl enable --now petguardian-camera.service

Check:

    systemctl status petguardian-camera.service

Logs:

    journalctl -u petguardian-camera.service -f

Stop:

    sudo systemctl stop petguardian-camera.service

Start:

    sudo systemctl start petguardian-camera.service


===============================================================================
11. BLE PYTHON ENVIRONMENT
===============================================================================

BLE uses:

    bleak

Create a dedicated virtual environment:

    python3 -m venv ~/petguardian-ble

Activate:

    source ~/petguardian-ble/bin/activate

Install:

    pip install bleak

Verify:

    pip show bleak

Do not commit the virtual environment. Each developer should create it locally.


-------------------------------------------------------------------------------
11.1 BLE TEST SCRIPT
-------------------------------------------------------------------------------

The file:

    petguardian_ble_scan.py

is a manual calibration/test script.

Example:

    source ~/petguardian-ble/bin/activate
    python3 /home/<USER>/pet-guardian/ble/petguardian_ble_scan.py


-------------------------------------------------------------------------------
11.2 BLE NODE-RED SCRIPT
-------------------------------------------------------------------------------

The file:

    petguardian_ble_nodered.py

outputs newline-delimited JSON for Node-RED.

Example output:

    {"name":"BCPro_217898","rssi":-57,"average_rssi":-56.4,"status":"Very Near"}

Recommended Node-RED Exec command:

    /home/<USER>/petguardian-ble/bin/python /home/<USER>/pet-guardian/ble/petguardian_ble_nodered.py

Configure Exec for:

    while the command is running / spawn mode

Recommended startup:

    Inject once after 4 seconds
    Repeat: none


-------------------------------------------------------------------------------
11.3 BLE JSON BUFFER FUNCTION
-------------------------------------------------------------------------------

If Node-RED reports:

    Unexpected end of JSON input

place a Function node between Exec and JSON:

    let buffer = context.get("buffer") || "";

    buffer += msg.payload.toString();

    let lines = buffer.split(/\r?\n/);

    context.set("buffer", lines.pop());

    let messages = [];

    for (let line of lines) {
        line = line.trim();

        if (line.length > 0) {
            messages.push({
                payload: line
            });
        }
    }

    return [messages];


===============================================================================
12. INSTALL OPENCV
===============================================================================

OpenCV handles:

- Reading camera frames
- Image preprocessing
- Loading the MobileNet-SSD model
- Neural-network inference
- Reading detection results

Install:

    sudo apt install -y python3-opencv python3-numpy

Verify:

    python3 -c "import cv2; print(cv2.__version__)"


===============================================================================
13. INSTALL MOBILENET-SSD
===============================================================================

MobileNet-SSD is the pretrained computer-vision object-detection model.

It is NOT an LLM.

The reference model recognizes a fixed set of object classes, including cat
and dog.

Download it:

    mkdir -p ~/petguardian-ai
    cd ~/petguardian-ai

    git clone https://github.com/chuanqi305/MobileNet-SSD.git

Primary files used by Pet Guardian:

    deploy.prototxt
    mobilenet_iter_73000.caffemodel

For reproducible builds, optionally pin the repository to a known Git commit.


===============================================================================
14. PET DETECTION
===============================================================================

Manual test script:

    pet_detect.py

Node-RED integration script:

    pet_detect_nodered.py

Reference stream:

    http://127.0.0.1:8000/stream.mjpg

OpenCV captures frames:

    cv2.VideoCapture(...)
    cap.read()

OpenCV preprocesses:

    cv2.dnn.blobFromImage(...)

OpenCV runs MobileNet-SSD:

    net.setInput(blob)
    detections = net.forward()

Pet Guardian filters detections to:

    cat
    dog

Example Node-RED JSON:

    {"status":"Dog Detected","pet":"dog","confidence":91.7}

or:

    {"status":"No Pet Detected","pet":null,"confidence":0}


-------------------------------------------------------------------------------
14.1 PET DETECTION NODE-RED EXEC
-------------------------------------------------------------------------------

Recommended Exec command:

    /usr/bin/python3 /home/<USER>/pet-guardian/ai/pet_detect_nodered.py

Configure:

    while the command is running / spawn mode

Recommended startup:

    Inject once after 6 seconds
    Repeat: none


-------------------------------------------------------------------------------
14.2 PET DETECTION JSON BUFFER
-------------------------------------------------------------------------------

Use the same buffering Function described in the BLE section if Node-RED
reports:

    Unexpected end of JSON input


===============================================================================
15. SQLITE DATABASE
===============================================================================

Node-RED package:

    node-red-node-sqlite

Reference database:

    /home/<USER>/petguardian.db

Do not normally commit the runtime database. Let each developer create a fresh
local database.


-------------------------------------------------------------------------------
15.1 PET STATUS TABLE
-------------------------------------------------------------------------------

Reference schema:

    CREATE TABLE IF NOT EXISTS pet_status (
        id INTEGER PRIMARY KEY,
        pet TEXT,
        confidence REAL,
        last_seen TEXT
    );


-------------------------------------------------------------------------------
15.2 SAVE PET SIGHTING
-------------------------------------------------------------------------------

Recommended prepared statement:

    INSERT INTO pet_status (id, pet, confidence, last_seen)
    VALUES (1, $pet, $confidence, $last_seen)
    ON CONFLICT(id) DO UPDATE SET
        pet = excluded.pet,
        confidence = excluded.confidence,
        last_seen = excluded.last_seen;

Function example:

    msg.params = {
        $pet: pet,
        $confidence: msg.payload.confidence,
        $last_seen: new Date(now).toISOString()
    };

The reference flow writes about once every 10 seconds while a pet remains
visible to avoid unnecessary SD-card writes.


-------------------------------------------------------------------------------
15.3 RESTORE LAST SEEN
-------------------------------------------------------------------------------

On startup:

    SELECT last_seen
    FROM pet_status
    WHERE id = 1;

Recommended startup:

    Inject once after 8 seconds
    Repeat: none


===============================================================================
16. BME280 ENVIRONMENT SENSOR
===============================================================================

Enable I2C:

    sudo raspi-config

Then:

    Interface Options
      -> I2C
      -> Enable

Install tools:

    sudo apt install -y i2c-tools

Detect:

    sudo i2cdetect -y 1

Reference:

    Bus: 1
    Address: 0x77

Recommended Node-RED Inject:

    Inject once after 2 seconds
    Repeat every 5 seconds


===============================================================================
17. RECOMMENDED STARTUP SEQUENCE
===============================================================================

Reference Node-RED startup timing:

    1 sec  -> Initialize SQLite
    2 sec  -> Start BME280 polling
    4 sec  -> Start BLE scanner
    6 sec  -> Start pet detector
    8 sec  -> Restore Last Seen

Camera startup is handled by:

    petguardian-camera.service

BLE and AI Exec nodes are long-running processes. Start them once; do not set
their Inject nodes to repeat.


===============================================================================
18. DASHBOARD
===============================================================================

Dashboard package:

    @flowfuse/node-red-dashboard

Reference sections:

Live Check-In:
- Live camera
- Pet confidence
- Last Seen
- Pet Status

Pet Environment:
- Temperature
- Temperature status
- Humidity
- Humidity status

Pet Proximity:
- RSSI signal strength
- Proximity status


-------------------------------------------------------------------------------
18.1 CAMERA TEMPLATE
-------------------------------------------------------------------------------

Example Dashboard 2.0 Template widget:

    <div style="text-align:center;">
        <img
            src="http://<PI-IP>:8000/stream.mjpg"
            style="
                width:100%;
                height:340px;
                object-fit:contain;
                border-radius:10px;
            "
        >
    </div>

Adjust height and object-fit to fit the local dashboard layout.


===============================================================================
19. REFERENCE BLE PROXIMITY VALUES
===============================================================================

Original BC04P calibration:

    1 ft   -> approximately -56 dBm
    6 ft   -> approximately -72 dBm
    20 ft  -> approximately -83 dBm

Reference thresholds:

    >= -62 dBm       Very Near
    -63 to -76 dBm   Near
    -77 to -86 dBm   Far
    < -86 dBm        Very Far / Weak

BLE RSSI is not an exact distance measurement. Recalibrate if room-level
behavior matters.


===============================================================================
20. VERIFY AFTER REBOOT
===============================================================================

Reboot:

    sudo reboot

Then verify:

1. Node-RED

    systemctl status nodered.service

2. Camera server

    systemctl status petguardian-camera.service

3. Camera stream

    http://<PI-IP>:8000

4. Dashboard

    http://<PI-IP>:1880/dashboard/page1

5. BME280 values update.

6. BLE proximity updates.

7. Pet detection runs.

8. Last Seen restores from SQLite.


===============================================================================
21. USEFUL TROUBLESHOOTING
===============================================================================

Node-RED status:

    systemctl status nodered.service

Node-RED logs:

    journalctl -u nodered.service -f

Camera status:

    systemctl status petguardian-camera.service

Camera logs:

    journalctl -u petguardian-camera.service -f

Camera list:

    rpicam-hello --list-cameras

Camera test:

    rpicam-hello

Bluetooth:

    bluetoothctl

Inside bluetoothctl:

    power on
    scan on

BME280/I2C:

    sudo i2cdetect -y 1

SQLite CLI:

    sqlite3 /home/<USER>/petguardian.db

Then:

    SELECT * FROM pet_status;


===============================================================================
22. FILES THAT SHOULD NOT NORMALLY BE COMMITTED
===============================================================================

Do not normally commit:

- Python virtual environments
- node_modules/
- SQLite runtime databases
- ~/.node-red runtime files unless intentionally packaged
- logs
- caches
- shell history
- temporary files

Example .gitignore:

    petguardian-ble/
    node_modules/
    *.db
    __pycache__/
    *.pyc
    .DS_Store


===============================================================================
23. REFERENCE PROJECT FILES TO DISTRIBUTE
===============================================================================

Camera:
    petguardian_camera.py

BLE:
    petguardian_ble_nodered.py
    petguardian_ble_scan.py        (optional test utility)

AI:
    pet_detect_nodered.py
    pet_detect.py                  (optional test utility)

Node-RED:
    exported JSON flow templates

Setup:
    README.txt
    optional petguardian-camera.service template


===============================================================================
24. THIRD-PARTY MODEL / LICENSE NOTE
===============================================================================

MobileNet-SSD is a third-party project/model.

If upstream model files are redistributed with this repository, preserve the
applicable upstream license and attribution.

If the model is downloaded during setup, developers should still review the
upstream license before production/commercial use.


===============================================================================
25. PRODUCTION HARDENING NOTES
===============================================================================

This is a hackathon/prototype architecture.

For production, consider:

- Node-RED/dashboard authentication
- HTTPS/TLS
- Firewall/network restrictions
- Secure configuration/secrets
- Better reconnect/retry logic
- Historical telemetry tables
- Process health monitoring
- Automated setup scripts
- Containerization where appropriate
- AI model optimization/hardware acceleration
- Individual pet recognition if required

Current AI behavior recognizes the class:

    cat
    dog

It does not identify a specific pet by name or identity.


===============================================================================
END
===============================================================================
