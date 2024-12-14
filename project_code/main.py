from my_streamlit import streamlit_interface
import asyncio

import requests
import xml.etree.ElementTree as ET

# Load XML from a local file 
with open("prompts.xml", "r", encoding="utf-8") as file:
    xml_content = file.read()

try:
    root = ET.fromstring(xml_content)
    for task in root.findall('task'):
        print(task.get('type'))
except ET.ParseError as e:
    print(f"XML parsing error: {e}")

asyncio.run(streamlit_interface())
