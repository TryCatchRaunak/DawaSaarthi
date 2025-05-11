__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import os
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from crewai import Agent
from crewai_tools import SerperDevTool
from crewai_tools import FirecrawlSearchTool
import sqlite3
import uuid
import datetime


from crewai import LLM
import litellm
import openai
import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from crewai_tools import FileWriterTool
import streamlit as st
load_dotenv()
# --- VISITOR TRACKING ---




import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
client = gspread.authorize(creds)

# Access the Google Sheet
sheet = client.open("Dawasaarthi_Visitors").sheet1

# Example: Append new visitor
import datetime
import uuid



search_tool = SerperDevTool()


model = genai.GenerativeModel('gemini-2.0-flash-001')

st.set_page_config(
    page_title="DawaSaarthi - Home Page"
)




# --- Accurate Visitor Tracking using Cookie (Place right after st.set_page_config) ---
from streamlit_javascript import st_javascript
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Setup Google Sheet
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
client = gspread.authorize(creds)
sheet = client.open("Dawasaarthi_Visitors").sheet1

# JavaScript for persistent cookie-based visitor ID
js_code = """
(() => {
  const cookieName = "visitor_id";
  let value = document.cookie.match('(^|;)\\s*' + cookieName + '\\s*=\\s*([^;]+)');
  if (value) {
    return value.pop();
  } else {
    const uuid = self.crypto.randomUUID();
    const expiry = new Date();
    expiry.setDate(expiry.getDate() + 365); // 1 year expiry
    document.cookie = `${cookieName}=${uuid}; path=/; expires=${expiry.toUTCString()}`;
    return uuid;
  }
})();
"""

visitor_id = st_javascript(js_code=js_code)

if visitor_id:
    existing_ids = sheet.col_values(1)  # Column A = visitor IDs
    if visitor_id not in existing_ids:
        sheet.append_row([visitor_id, datetime.datetime.now().isoformat()])
        st.info("✅ New visitor recorded.")
    else:
        st.info("👋 Returning visitor (cookie-based).")








with st.sidebar:
    st.title("Enquiry Booth")
    st.markdown("------")
    uploaded_file = st.file_uploader("Upload your prescription...", type=['jpg', 'jpeg', 'png'])
    generate_comparison = st.button("Generate Output", type="primary", use_container_width=True)
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image")
    medicines=st.text_area("Medicines To Be Searched", height=100)
    generate_comparison_manual=st.button("Generate Output Manually", type="primary", use_container_width=True)  

# Prompts for AI
medicine_prompt = """
First recognize the medicine names written on the prescription and then check for spelling mistakes and give the correct existing medicine names in return in a comma seperated format.
"""

topic=medicine_prompt
def get_gemini_response(input, image):
        response = model.generate_content([input, image[0]])
        return response.text

def input_image_setup(uploaded_file):
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            image_parts = [{
                "mime_type": uploaded_file.type,
                "data": bytes_data
            }]
            return image_parts
        return None
def agents_workflow(uploaded_file,topic):
        if uploaded_file is not None:
            image_data = input_image_setup(uploaded_file)
            medicine_name = get_gemini_response(topic,image_data)
        researcher = Agent(
            role="Senior Researcher",
            goal=(
                f"You are an expert in searching and finding direct purchase links for the list of medicines {medicine_name} from the authentic online pharmacies .Generate the links for all the medicines one by one and return them to the user."   
            ),
            backstory=(
            "You're a seasoned researcher who goes out in the web to surf and find out the direct links to the medicines given and return them to the user for them to buy."
            ),
            tools=[search_tool,FirecrawlSearchTool()],
            verbose=True,
        )

        reporting_analyst = Agent(
            role="Research Reporter",
            goal=(
                "Create a report consisting the link of the medicines that redirects to the page of the medicine purchase.If you cannot complete the request due to tool limitations or missing data, return whatever results you can, clearly marking gaps. Do not skip medicines entirely.Write in the tabular format."
            ),
            backstory=(
                "You are a meticulous writer who writes down the links to the medicines that are required by the user and creates a report for them to buy the medicines from the link provided."
            ),
        )

        research_task = Task(
            description=(
                f"Perform searches like buy {medicine_name} from online pharmacy and get the links to the medicines from the online pharmacies like 1mg, Apollo Pharmacy, Netmeds etc. and return them to the user.It should be done for all the medicines one by one and return them to the user. Also state the limitation that you are facing in this environemnt.Search for links acroos various stores and provide them."
            ),
            expected_output=(
                "Link to the medicines provided by the user to directly get redirected to the page of the medicine and order from it"
            ),
            agent=researcher,
            iterations=len(medicines.split()),
            verbose=True,
        )

        reporting_task = Task(
            description=(
                f"Accumulate all the links researched by the previous agent for the medicines {medicine_name} and create a report in a structured format.Give the output in hepyerlinked format not in html format"
            ),
            expected_output=(
            "A report consisting the links to the medicines that are required by the user and the link to the page of the medicine purchase in a hyperlinked format."
        
            ),
            agent=reporting_analyst,
            output_file="Links.md",
            tools=[search_tool,FirecrawlSearchTool()]
        )

        # Initialize and execute the Crew
        crew = Crew(
            agents=[
                researcher,
                reporting_analyst
            ],
            tasks=[
                research_task,
                reporting_task
            ],
            process=Process.sequential,
            verbose=True,
        )
        final_report=crew.kickoff()
        
        return final_report

def agents_workflow_manual():
        researcher = Agent(
            role="Senior Researcher",
            goal=(
                f"You are an expert in searching and finding direct purchase links for the list of medicines {medicines} from the authentic online pharmacies .Generate the links for all the medicines one by one and return them to the user."   
            ),
            backstory=(
            "You're a seasoned researcher who goes out in the web to surf and find out the direct links to the medicines given and return them to the user for them to buy."
            ),
            tools=[search_tool],
            verbose=True,
        )

        reporting_analyst = Agent(
            role="Research Reporter",
            goal=(
                "Create a report consisting the link of the medicines that redirects to the page of the medicine purchase.If you cannot complete the request due to tool limitations or missing data, return whatever results you can, clearly marking gaps. Do not skip medicines entirely.Write in the tabular format."
            ),
            backstory=(
                "You are a meticulous writer who writes down the links to the medicines that are required by the user and creates a report for them to buy the medicines from the link provided."
            ),
        )

        research_task = Task(
            description=(
                f"Perform searches like buy {medicines} from online pharmacy and get the links to the medicines from the online pharmacies like 1mg, Apollo Pharmacy, Netmeds etc. and return them to the user.It should be done for all the medicines one by one and return them to the user. Also state the limitation that you are facing in this environemnt.Search for links acroos various stores and provide them."
            ),
            expected_output=(
                "Link to the medicines provided by the user to directly get redirected to the page of the medicine and order from it"
            ),
            agent=researcher,
            iterations=len(medicines.split()),
            verbose=True,
        )

        reporting_task = Task(
            description=(
                f"Accumulate all the links researched by the previous agent for the medicines and create a report in a structured format.Give the output in hepyerlinked format not in html format"
            ),
            expected_output=(
            "A report consisting the links to the medicines that are required by the user and the link to the page of the medicine purchase in a hyperlinked format."
        
            ),
            agent=reporting_analyst,
            output_file="Links.md",
            tools=[search_tool]
        )

        crew = Crew(
            agents=[
                researcher,
                reporting_analyst
            ],
            tasks=[
                research_task,
                reporting_task
            ],
            process=Process.sequential,
            verbose=True,
        )
        final_report=crew.kickoff()
        
        return final_report


# Main App Layout
st.title("DawaSaarthi")

if generate_comparison:
    with st.spinner("Listing Down Links... This may take a moment..."):
        try:
            if uploaded_file is not None:
                result = agents_workflow(uploaded_file,topic)
                if result:
                    st.success("Medicine report generated successfully!")
                    with open("Links.md", "r",encoding="utf-8") as f:
                        link_content = f.read()
                    with st.expander("View report", expanded=True):
                        st.markdown(result)
                    with open("Links.md", "rb") as f:
                        st.download_button(
                            label="Report Download",
                            data=f,
                            file_name="Links.md",
                            mime="text/markdown"
                        )
            else:
                st.error("Please upload a prescription to proceed.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if generate_comparison_manual:
    with st.spinner("Listing Down Links... This may take a moment..."):
        try:
                result = agents_workflow_manual()
                if result:
                    st.success("Medicine report generated successfully!")
                    with open("Links.md", "r",encoding="utf-8") as f:
                        link_content = f.read()
                    with st.expander("View report", expanded=True):
                        st.markdown(result)
                    with open("Links.md", "rb") as f:
                        st.download_button(
                            label="Report Download",
                            data=f,
                            file_name="Links.md",
                            mime="text/markdown"
                        )
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

st.markdown("-----------")
st.markdown("Team Nexora")
