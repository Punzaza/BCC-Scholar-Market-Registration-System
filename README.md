
# BCC Scholar Market Registration System

Welcome to the GitHub repository for the Registration System used in the BCC Scholar Market event, an academic day hosted by Bangkok Christian College.

This system was designed to facilitate registration through LINE, a popular social media platform in Thailand, and a website. The system was able to handle more than 1,500 users during the event and proved to be an effective tool in managing the registration process.

However, please keep in mind that the authors of this project were only in grade 11, so the level of perfection may not be as high as expected. This repository serves as a reference for those interested in the implementation and functionality of the system. The registration process was implemented through the use of LINE Official Account which was linked with the Python code, while the website was written in HTML.

Additionally, we also provide the workflow for the system. Please note that some parts of it are written in Thai. We hope it will be useful for your reference.

## Structure
The registration system is structured using the Python library Flask as the main function. Flask is a micro web framework written in Python, it allows us to create web applications easily with Python. It provides useful tools and features for handling requests and responses, routing, and template management. The system's structure is divided into two sections, the "before-event" version and the "event" version. Each version has its own set of functions and templates to handle the registration process and QR code scanning during the event.

The "before-event" version was used for pre-registration and registering attendance to the actual event, while the "event" version was used in conjunction with a QR code scanner application (not included in this repository) for ticket checking during the event.

One of the key features of the system is that we link the ticketId (used for QR code) with Google Sheets. This allows for easy access and management of the registered attendees' information. By linking the ticketId to Google Sheets, it makes it easy to check the attendance of the registrants during the event by scanning their QR code with a QR code scanner application.

In the production phase, we also used Gunicorn to handle the server requests. Gunicorn is a pre-fork worker model HTTP server, which means it forks multiple worker processes to handle the incoming requests, it can handle more number of clients at a time and increases the performance of the application.

Please note that during the development phrase, we used Python 3.11, so it's recommended to use the same version to avoid compatibility issues.

## Optimizations

We understand that the code may not meet the standards of optimization, but it was created within a limited time frame of two weeks. We hope that this repository will serve as a reference for others and demonstrate the progress that was made within the given time frame.


## Contributing

I want to be transparent and let you know that this is my first time creating a GitHub repository. I am still learning the process of accepting contributions, but I am open to suggestions and improvements to the project. If you have any ideas for optimization, please feel free to submit a contribution and I will review it with enthusiasm. 
## Used By

As mentioned above, this registration system was used in an academic day event, specifically the 170th school anniversary celebration which is hosted every 10 years by Bangkok Christian College. Our system consisted of 36 mini events that ranged in size from 10 attendants to 300 attendants.

## Installation

Install the required Python library using

```
pip install -r requirements.txt
```

Additionally, you will also need to provide the 'creds.json' under the folder keys/googleSheets, this serves as a key to connect to Google Sheets. For more information on how to create the credentials, please refer to the following link: https://developers.google.com/workspace/guides/create-credentials.

Furthermore, for the HTTPS connection, you will need to provide 'cert.pem' and 'key.key' under the folder keys/ssl. These files are used to encrypt the communication between the client and the server. Make sure you have the required certificates and keys to run the system.

As stated above, please also install Gunicorn. The usual command we used to run the program is

```
sudo gunicorn --bind 0.0.0.0:443 -w 5 --certfile=keys/ssl/cert.pem --keyfile=keys/ssl/key.key wsgi:app &
```

## Authors

- Project Director: Punpapol ([@Punzaza](https://www.github.com/Punzaza))
- Website Director: Pannatat
- UX/UI Directors: Wirachat, Phuwasit
- UX/UI Designers: Kittiphan, Punnawat, Poomipat, Arth
