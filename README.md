# Automatic-Applications-using-minimal-ai-
Might make it private... use while you can. This is testV5.0 - I'm currently using prod V2.0 , if you'd like that version please feel free to reach out. Some functionality has been added, some improved. Uploading this here for the sake of collaboration, and helping some other poor soul out there. Script can be used for more than applying to jobs. 


# Naukri Job Application Automation

## Description
This Python script automates the process of applying for jobs on Naukri.com using Selenium WebDriver and Google's Gemini AI model. It streamlines the job application process by automatically logging in, searching for jobs, and intelligently answering application questions.

## Features
- Automated login to Naukri.com - can be modified for any other platform... that's up to you to do. 
- Customizable job search with filters
- AI-powered responses to application questions using Google's Gemini model
- Handling of multiple job applications in a single run
- Detailed logging for monitoring and debugging

## Prerequisites
- Python 3.x
- Chrome WebDriver
- Selenium
- Google Gemini AI API key

## Installation
1. Clone the repository 
2. Install required packages -
   pip install selenium webdriver_manager python-dotenv google-generativeai

3. Set up environment variables:
Create a `.env` file in the project root with the following:



## Configuration
- Modify the `job_title` in the `search_jobs` method to target specific roles.
- Adjust the filters in the `search_jobs` method to refine job searches.
- Customize the applicant profile in the `system_instruction` for more accurate AI responses.

## Logging
The script logs its activities to `gemini_automation.log` for debugging and monitoring.

## Disclaimer
This script is for educational purposes only. Use responsibly and in accordance with Naukri.com's terms of service.

## Contributing
Contributions are welcome. Please fork the repository and submit a pull request with your changes.

## License
MIT etc etc - feel free to use it that's all 

## Author
SlightlyHappy 

## Last Updated
Sunday, February 16, 2025; for the record, fuck the job market be it EU, US, or India. 


