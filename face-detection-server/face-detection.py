import cv2
import face_recognition
import numpy as np
import os
import requests
import time

# Path to the folder where face images will be stored
faces_folder = "known_faces"
if not os.path.exists(faces_folder):
    os.makedirs(faces_folder)

# Load known face encodings and names from the folder
known_face_encodings = []
known_face_names = []

# Load faces from folder
for filename in os.listdir(faces_folder):
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        name = os.path.splitext(filename)[0]
        image = face_recognition.load_image_file(os.path.join(faces_folder, filename))
        face_encodings_in_image = face_recognition.face_encodings(image)
        
        if len(face_encodings_in_image) > 0:
            face_encoding = face_encodings_in_image[0]
            known_face_encodings.append(face_encoding)
            known_face_names.append(name)
        else:
            print(f"No faces found in the image: {filename}")

# Initialize variables for processing video frames
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True
face_counts = {name: 0 for name in known_face_names}
currently_visible = {name: False for name in known_face_names}  # Track face visibility status
last_seen_time = {name: 0 for name in known_face_names}  # Track last time face was seen
FRAME_THRESHOLD = 2  # Minimum number of seconds the person must be out of frame before the count increases

# Capture video from the webcam
video_capture = cv2.VideoCapture(0)

# URL for detecting object (returns 0 or 1)
url = "http://192.168.43.198/"

def check_object_detection():
    try:
        # Send a GET request to the server
        response = requests.get(url)
        
        # Check the response content, which is expected to be '0' or '1'
        if response.status_code == 200:
            return response.text.strip() == '1'  # Returns True if '1', otherwise False
        else:
            print(f"Failed to get a valid response. Status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return False

while True:
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Resize frame to 1/4 size for faster processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (OpenCV uses) to RGB color (face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Process every alternate frame to save computational power
    if process_this_frame:
        # Check if an object is detected via the API
        object_detected = check_object_detection()

        if object_detected:
            print("Object detected")
            
            # If an object is detected, proceed with face recognition
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            current_frame_visible = {name: False for name in known_face_names}  # Track faces in the current frame

            for face_encoding, face_location in zip(face_encodings, face_locations):
                # See if the face is a match for the known faces
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

                # Use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)

                if matches and matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    current_frame_visible[name] = True  # Mark face as visible in the current frame

                    # Update face visibility and count logic
                    current_time = time.time()
                    if not currently_visible[name]:
                        if current_time - last_seen_time[name] > FRAME_THRESHOLD:
                            face_counts[name] += 1
                        currently_visible[name] = True
                    last_seen_time[name] = current_time
                else:
                    # Handle new user registration
                    if name == "Unknown":
                        print("New face detected. Please enter the name:")
                        new_name = input()  # Get new name from the user

                        # Register the new user
                        known_face_encodings.append(face_encoding)
                        known_face_names.append(new_name)
                        face_counts[new_name] = 0  # Initialize count for the new user
                        current_frame_visible[new_name] = True  # Mark face as visible
                        last_seen_time[new_name] = time.time()  # Mark the current time as last seen

                face_names.append(name)

            # Update visibility for the next frame
            for name in currently_visible:
                if not current_frame_visible[name]:
                    currently_visible[name] = False  # Mark face as not visible if it wasn't detected in this frame
        else:
            print("No object detected")
            face_names = []

    process_this_frame = not process_this_frame

    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up the face locations since the frame was resized
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Display the name and count below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, f"{name}: {face_counts.get(name, 0)}", (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the video feed
    cv2.imshow('Video', frame)

    # Break the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture
video_capture.release()
cv2.destroyAllWindows()
