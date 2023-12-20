## Traffic Ticketing App

### Overview
The Traffic Ticketing App is a comprehensive solution designed for law enforcement agencies to streamline the process of issuing traffic tickets. 
Built using Streamlit, this app allows traffic officers to enter offense details, capture photographic evidence using a camera (planned), and store all information efficiently in a CockroachDB database. Tickets older grace period of 30 days after which the fine amount is doubled. Ticket overview in the admin page allows for filtering all tickets by status, offender, issuer, license plate etc. 
The app's intuitive interface and seamless integration of image capture and database storage make it an essential tool for modern traffic management particularly in emerging nations where traffic obedience is a sever challenge, 
and enforcement methods proved ineffective. 


### Features
- Offense Data Entry: Easy-to-use forms for entering various details about traffic offenses.
- Camera Integration: Officers can capture up to three images for each offense directly within the app.
- Real-Time Image Display: Captured images are displayed at the bottom of the page as they are taken.
- Persistent Data Storage: Offense details and images are stored securely in a CockroachDB database. (You may use any db of your choice for storing data)
- Responsive Design: Optimized for both desktop and mobile use.
- In the admin page view, see list of all tickets created and filter by name, officer, license plate etc


### Installation

#### Prerequisites
- Python 3.8 or higher
- Streamlit
- ConckroachDB (PostgreSQL)
- PIL (Python Image Library


#### Set Up

1. Clone the repo `git clone git@github.com:rnwokoye/sfaeroads.git`
2. Navigate to the app directory: `cd sfaeroads`
3. `pip install -r requirements.txt`


### Running The App
`streamlit run app.py`

### Usage
1. Start the app and navigate to the URL provided by Streamlit.
2. Enter the offense details in the provided form fields.
3. ~~Use the camera input to capture images related to the offense.~~
4. Review the captured images displayed on the screen.
5. Submit the form to save the offense details and images to the database.


### Contributing
Contributions to the Traffic Ticketing App are welcome. I still need to add a picture capture and upload module :-) 

### License
This project is licensed under the MIT License - see the LICENSE file for details.

##### Contact
rnwokoye@gmail.com

Project Link: https://github.com/rnwokoye/sfaeroads
