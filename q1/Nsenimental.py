import tkinter as tk
from tkinter import filedialog, messagebox
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from PyPDF2 import PdfReader
import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which
import threading
from tkinter.ttk import Progressbar

# Set FFmpeg converter path explicitly (if required)
AudioSegment.converter = which("ffmpeg")

# Function to convert any audio file to .wav format
def convert_audio_to_wav(file_path):
    try:
        audio = AudioSegment.from_file(file_path)
        wav_file_path = file_path.rsplit(".", 1)[0] + ".wav"
        audio.export(wav_file_path, format="wav")
        return wav_file_path
    except Exception as e:
        raise ValueError(f"Could not convert audio file: {e}")

# Function to extract text from a PDF file
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to transcribe audio to text
def extract_text_from_audio(file_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
        return text
    except Exception as e:
        raise ValueError(f"Could not process the audio file: {e}")

# Function to update progress bar
def update_progress(progress, value):
    progress["value"] = value
    root.update_idletasks()

# Function to process the uploaded file and perform sentiment analysis
def analyze_sentiment():
    file_path = filedialog.askopenfilename(
        filetypes=[
            ("Text files", "*.txt"),
            ("PDF files", "*.pdf"),
            ("Audio files", "*.mp3 *.wav *.ogg *.aac *.flac"),
        ]
    )
    if not file_path:
        return

    # Reset progress bar and status
    progress["value"] = 0
    status_label.config(text="Processing...")

    # Function to process file in a separate thread
    def process_file(file_path):
        try:
            total_steps = 3  # Define total number of steps in the process
            current_step = 1

            # Step 1: Read the file content
            update_progress(progress, (current_step / total_steps) * 100)
            if file_path.endswith(".txt"):
                with open(file_path, "r") as file:
                    reviews = file.readlines()
            elif file_path.endswith(".pdf"):
                reviews = extract_text_from_pdf(file_path).split("\n")
            elif file_path.endswith((".mp3", ".ogg", ".aac", ".flac", ".wav")):
                # Convert audio to .wav if necessary
                if not file_path.endswith(".wav"):
                    file_path = convert_audio_to_wav(file_path)
                reviews = extract_text_from_audio(file_path).split(".")  # Split sentences
            else:
                messagebox.showerror("Error", "Unsupported file type!")
                return

            current_step += 1  # Move to next step

            # Step 2: Perform sentiment analysis
            update_progress(progress, (current_step / total_steps) * 100)
            sid = SentimentIntensityAnalyzer()
            sentiment_scores = [sid.polarity_scores(review) for review in reviews if review.strip()]
            sentiment_scores_rounded = [round(score["compound"], 1) for score in sentiment_scores]
            sentiment_labels = [
                "negative" if score < 0 else "positive" if score > 0 else "neutral"
                for score in sentiment_scores_rounded
            ]
            sentiment_distribution = {
                label: sentiment_labels.count(label)
                for label in set(sentiment_labels)
            }

            # Step 3: Update results in the GUI
            update_progress(progress, 100)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "Sentiment Scores:\n")
            result_text.insert(tk.END, f"{sentiment_scores_rounded}\n\n")
            result_text.insert(tk.END, "Sentiment Labels:\n")
            result_text.insert(tk.END, f"{sentiment_labels}\n\n")
            result_text.insert(tk.END, "Sentiment Distribution:\n")
            result_text.insert(tk.END, f"{sentiment_distribution}\n")

            status_label.config(text="Analysis Complete!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            status_label.config(text="Error occurred.")
        finally:
            update_progress(progress, 100)

    # Run the file processing in a separate thread to avoid freezing the GUI
    threading.Thread(target=process_file, args=(file_path,)).start()

# Create the main GUI window
root = tk.Tk()
root.title("Sentiment Analysis Tool")

# Create a button to upload the file
upload_button = tk.Button(root, text="Upload File", command=analyze_sentiment)
upload_button.pack(pady=10)

# Create a progress bar
progress = Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress.pack(pady=10)

# Create a label to show status of the process
status_label = tk.Label(root, text="Please upload a file to start.", font=("Helvetica", 10))
status_label.pack(pady=5)

# Create a text widget to display the results
result_text = tk.Text(root, wrap=tk.WORD, width=80, height=20)
result_text.pack(pady=10)

# Run the GUI event loop
root.mainloop()
