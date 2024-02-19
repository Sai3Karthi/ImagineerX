import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, time
from vertexai import init
from vertexai.preview.generative_models import GenerativeModel

app = Flask(__name__)
app = Flask(__name__, static_folder='static')
excel_file_path = "ImagineerX_final\\get_calendar_info\\testdata.xlsx"
df = pd.read_excel(excel_file_path)

# Set the path to the service account key file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "iron-burner-412609-1de637da5b5f.json"

def summarize_reviews(schedule_data, user_start_time_str):
    try:
        # Convert user_start_time to datetime.time object
        user_start_time = datetime.strptime(user_start_time_str, '%H:%M').time()

        # Extract relevant information from the schedule_data DataFrame
        days_users_available = []
        for day, start_col, end_col in [('Monday', 'Monday (Start)', 'Monday (End)'),
                                        ('Tuesday', 'Tuesday (Start)', 'Tuesday (End)'),
                                        ('Wednesday', 'Wednesday (Start)', 'Wednesday (End)'),
                                        ('Thursday', 'Thursday (Start)', 'Thursday (End)'),
                                        ('Friday', 'Friday (Start)', 'Friday (End)')]:
            # Filter users available after user_start_time
            users_available = schedule_data.loc[(schedule_data[start_col].notna()) & 
                                                (schedule_data[start_col].apply(lambda x: x.strftime('%H:%M')).ge(user_start_time_str)),
                                                ['Name', start_col, end_col]]
            days_users_available.append("{}:\n{}".format(day, users_available.to_string(index=False)))

        earliest_availability = schedule_data[['Monday (Start)', 'Tuesday (Start)', 'Wednesday (Start)', 'Thursday (Start)', 'Friday (Start)']].idxmin(axis=1)
        best_day = earliest_availability.idxmin()
        best_time = "{} {}: {} : {}".format(best_day,
                                            schedule_data.loc[earliest_availability.idxmin(), earliest_availability[earliest_availability.idxmin()]].strftime("%A"),
                                            schedule_data.loc[earliest_availability.idxmin(), earliest_availability[earliest_availability.idxmin()]].strftime("%H:%M"),
                                            schedule_data.loc[earliest_availability.idxmin(), earliest_availability[earliest_availability.idxmin()].split(' ')[0] + ' (End)'].strftime("%H:%M"))

        # Initialize Vertex AI
        init()

        # Initialize the GenerativeModel
        model = GenerativeModel("gemini-pro-vision")

        # Fixed prompt
        prompt = "MAINTAIN THE GIVEN STRUCTURE. GOAL: Analyze the starting and ending work time (users are available within that time) of each user for each day in the provided schedule data and provide the best date and time to conduct a meeting based on the most number of users available .Output is strictly restricted to two outputs 1) best time to conduct meeting in the format 'day:time'.2) why this is the best time.\n\nDays and Users Available:\n{}\nBest Time to Conduct Meeting:\n{}".format('\n'.join(days_users_available), best_time)

        # Generate content based on the prompt
        responses = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.4,
                "top_p": 1,
                "top_k": 32
            },
            stream=True
        )

        generated_output = ""
        for response in responses:
            generated_output += response.text + "\n"

        return generated_output

    except Exception as e:
        return "Error occurred: {}".format(e)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # If the button "get started" is clicked, redirect to the login route
        if request.form.get('get_started'):
            return redirect(url_for('login'))
    # Render the register.html template for GET requests or when the "get started" button is not clicked
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global df
    if request.method == 'POST':
        # Get the email and password from the form
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the email exists in the DataFrame and if the password matches
        user_data = df[df['email'] == email]

        if user_data.empty or user_data.iloc[0]['password'] != password:
            # If the email or password is incorrect, render the login.html template with an error message
            return render_template('login.html', message='Invalid email or password. Please try again.')
        else:
            # If login is successful, render the dashboard.html template with the user's data
            return render_template('home/home.html', user=user_data.iloc[0])
    # Render the login.html template for GET requests or when login fails
    return render_template('login.html', message='')

@app.route('/signup')
def signup():
    return render_template('signup.html', message='')
@app.route('/signup_process', methods=['POST'])
def signup_process():
    global df
    email = request.form.get('email')
    password = request.form.get('password')
    username = request.form.get('username')

    # Check if email or username already exists
    if (df['email'] == email).any() or (df['Name'] == username).any():
        return render_template('signup.html', message='Email or username already exists. Please choose a different one.')

    # Add new user to the DataFrame
    new_user = pd.DataFrame({'Name': [username], 'email': [email], 'password': [password]})
    df = pd.concat([df, new_user], ignore_index=True)

    # Update the Excel file
    df.to_excel(excel_file_path, index=False)

    return redirect(url_for('home'))

@app.route('/home', methods=['GET', 'POST'])
def home():
        return render_template('home/home.html')

@app.route('/table', methods=['GET', 'POST'])
def display_table():
    try:
        # Read the predefined Excel file
        excel_file_path = "ImagineerX_final\\get_calendar_info\\testdata.xlsx"  # Replace with the path to your predefined Excel file
        df = pd.read_excel(excel_file_path)

        # Convert DataFrame to HTML table
        html_table = df.to_html(index=False, classes='data')

        # Render the HTML template with the table
        return render_template('table/table.html', table=html_table)
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/aicaller', methods=['GET', 'POST'])
def aicaller():
    if request.method == 'POST':
        try:
            user_start_time = request.form['start_time']
            # Read Excel file using pandas
            excel_file_path = "ImagineerX_final\\get_calendar_info\\testdata.xlsx"  # Replace with the path to your Excel file
            print("Current Working Directory:", os.getcwd())
            schedule_data = pd.read_excel(excel_file_path)

            # Pass schedule_data and user_start_time to summarize_reviews function
            generated_output = summarize_reviews(schedule_data, user_start_time)

            return render_template('index.html', output=generated_output)
        except Exception as e:
            # Handle any errors that occur during file reading or processing
            return render_template('index.html', output=f"Error: {e}")

    # If method is GET or no file is processed yet, render the template with empty output
    return render_template('index.html', output="")


if __name__ == "__main__":
    app.run(debug=True)
    os.getcwd()
