Project: Multi-thread Web Server
Course: Comp 2322 Computer Networking

Environment Requirements:
- Python 3.6 or above.
- Standard libraries: socket, threading, os, time, email.utils, urllib.parse.

How to Run the Server:
1. Open a terminal/command prompt on the host machine.
2. Navigate to the folder containing `server.py`.
3. Run the command: python server.py
4. The server will now listen on 0.0.0.0:8080, making it accessible to any device on the same local network.

How to Connect from Different Hosts (Project Requirement):
To test the server from another device (e.g., a phone or a second laptop), follow these steps:

1. Find the Server's Local IP:
   - On Windows: Type `ipconfig` in CMD and look for "IPv4 Address" under your Wi-Fi adapter.

2. Access via Browser:
   - On the SECOND device, open a web browser.
   - In the address bar, type: http://<SERVER_IP>:8080/index.html
     (Example: http://192.168.13.254:8080/index.html)

3. Testing Functions:
   - GET Text: Access http://<SERVER_IP>:8080/index.html
   - GET Image: Access http://<SERVER_IP>:8080/test.jpg (ensure test.jpg is in the 'www' folder)
   - 404 Error: Access a non-existent file like http://<SERVER_IP>:8080/none.html

Verification:
Check the `server.log` on the server machine. You should see entries showing the IP address of your second device instead of 127.0.0.1, proving successful cross-host communication.