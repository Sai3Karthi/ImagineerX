import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, time
from vertexai import init
from vertexai.preview.generative_models import GenerativeModel

app = Flask(__name__)

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
def register():
        return render_template('register.html')  # Render the initial HTML file with 'next' button

@app.route('/login_business', methods=['GET', 'POST'])
def login_business():
    if request.method == 'POST':
        return redirect(url_for('home'))  # Redirect to index route when 'get started' button is clicked
    else:
        return render_template('login_business.html')  # Render the initial HTML file with 'login' button

@app.route('/login_personal', methods=['GET', 'POST'])
def login_personal():
    if request.method == 'POST':
        return redirect(url_for('home'))  # Redirect to index route when 'get started' button is clicked
    else:
        return render_template('login_personal.html')  # Render the initial HTML file with 'login' button

@app.route('/home', methods=['GET', 'POST'])
def home():
        return render_template('home/home.html')

@app.route('/table', methods=['GET', 'POST'])
def display_table():
    try:
        # Read the predefined Excel file
        excel_file_path = "testdata.xlsx"  # Replace with the path to your predefined Excel file
        df = pd.read_excel(excel_file_path)

        # Convert DataFrame to HTML table
        html_table = df.to_html(index=False, classes='data')

        # Render the HTML template with the table
        return render_template('table.html', table=html_table)
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            user_start_time = request.form['start_time']
            # Read Excel file using pandas
            excel_file_path = "testdata.xlsx"  # Replace with the path to your Excel file
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
