import streamlit as st
import requests
import base64
import io
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

##########
##### Set up sidebar.
##########

# Add in location to select image.
st.sidebar.write('#### Select an image to upload.')
uploaded_file = st.sidebar.file_uploader('',
                                         type=['png', 'jpg', 'jpeg'],
                                         accept_multiple_files=False)

st.sidebar.write('[Find additional images on Roboflow.](https://public.roboflow.com/object-detection/bccd/)')

## Add in sliders.
confidence_threshold = st.sidebar.slider('Confidence threshold: What is the minimum acceptable confidence level for displaying a bounding box?', 0.0, 1.0, 0.5, 0.01)
overlap_threshold = st.sidebar.slider('Overlap threshold: What is the maximum amount of overlap permitted between visible bounding boxes?', 0.0, 1.0, 0.5, 0.01)

image = Image.open('./images/roboflow_logo.png')
st.sidebar.image(image, use_column_width=True)

image = Image.open('./images/streamlit_logo.png')
st.sidebar.image(image, use_column_width=True)

##########
##### Set up main app.
##########

## Title.
st.write('# Blood Cell Count Object Detection')

## Pull in default image or user-selected image.
if uploaded_file is None:
    # Default image.
    url = 'https://github.com/matthewbrems/streamlit-bccd/blob/master/BCCD_sample_images/BloodImage_00038_jpg.rf.6551ec67098bc650dd650def4e8a8e98.jpg?raw=true'
    image = Image.open(requests.get(url, stream=True).raw)
else:
    # User-selected image.
    image = Image.open(uploaded_file)

## Subtitle.
st.write('### Inferenced Image')

# Convert to JPEG Buffer.
buffered = io.BytesIO()
image.save(buffered, quality=90, format='JPEG')

# Base 64 encode.
img_str = base64.b64encode(buffered.getvalue()).decode('ascii')

## Construct the URL to retrieve image.
upload_url = ''.join([
    'https://infer.roboflow.com/rf_U1BBNbuxDkXLZ5kZwnJh56P9gK82',
    f'?access_token={st.secrets["access_token"]}',
    '&format=image',
    f'&overlap={overlap_threshold * 100}',
    f'&confidence={confidence_threshold * 100}',
    '&stroke=2',
    '&labels=True'
])

## POST to the API.
r = requests.post(upload_url,
                  data=img_str,
                  headers={
                      'Content-Type': 'application/x-www-form-urlencoded'
                  })

# Check response status
if r.status_code == 200:
    try:
        # Try to open the image from the response content
        image = Image.open(io.BytesIO(r.content))
        
        # Display the image
        st.image(image, use_column_width=True)
        
        ## Construct the URL to retrieve JSON.
        json_url = ''.join([
            'https://infer.roboflow.com/rf_U1BBNbuxDkXLZ5kZwnJh56P9gK82',
            f'?access_token={st.secrets["access_token"]}'
        ])
        
        ## POST to the API for JSON response.
        r_json = requests.post(json_url, data=img_str, headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        
        # Check JSON response status
        if r_json.status_code == 200:
            ## Save the JSON.
            output_dict = r_json.json()
            
            ## Generate list of confidences.
            confidences = [box['confidence'] for box in output_dict['predictions']]
            
            ## Summary statistics section in main app.
            st.write('### Summary Statistics')
            st.write(f'Number of Bounding Boxes (ignoring overlap thresholds): {len(confidences)}')
            st.write(f'Average Confidence Level of Bounding Boxes: {np.round(np.mean(confidences), 4)}')

            ## Histogram in main app.
            st.write('### Histogram of Confidence Levels')
            fig, ax = plt.subplots()
            ax.hist(confidences, bins=10, range=(0.0, 1.0))
            st.pyplot(fig)

            ## Display the JSON in main app.
            st.write('### JSON Output')
            st.write(output_dict)
        else:
            st.error("Failed to retrieve JSON output.")
            st.write(r_json.json())  # Display any error messages from the API
            
    except Exception as e:
        st.error(f"Error opening image: {e}")
        st.write("Response content:", r.content)  # Display the raw response content for debugging
else:
    st.error("Failed to retrieve the image.")
    st.write(f"Response code: {r.status_code}")  # Display the status code for debugging
    st.write("Response content:", r.content)  # Display the raw response content for debugging
