from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Initialize Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize NLTK Sentiment Analyzer
sid = SentimentIntensityAnalyzer()

# Define database model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Pending")  # Pending, Accepted, Rejected
    sentiment = db.Column(db.String(20), nullable=True)  # Positive, Negative, Neutral
    scores = db.Column(db.Text, nullable=True)  # Sentiment scores in JSON format

# Create database tables
with app.app_context():
    db.create_all()

# Route: Home page for submitting reviews
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        review_content = request.form["review"]
        if review_content.strip():
            # Save review to database as "Pending"
            review = Review(content=review_content)
            db.session.add(review)
            db.session.commit()
        return redirect(url_for("index"))
    return render_template("index.html")

# Route: Admin dashboard for managing reviews
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    reviews = Review.query.all()
    return render_template("dashboard.html", reviews=reviews)

# Route: Accept a review and perform sentiment analysis
@app.route("/accept/<int:review_id>")
def accept_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.status == "Pending":
        # Perform sentiment analysis
        scores = sid.polarity_scores(review.content)
        sentiment = (
            "Positive" if scores["compound"] > 0 else
            "Negative" if scores["compound"] < 0 else
            "Neutral"
        )
        # Update review in the database
        review.status = "Accepted"
        review.sentiment = sentiment
        review.scores = str(scores)
        db.session.commit()
    return redirect(url_for("dashboard"))

# Route: Reject a review
@app.route("/reject/<int:review_id>")
def reject_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.status == "Pending":
        review.status = "Rejected"
        db.session.commit()
    return redirect(url_for("dashboard"))

# Route: View analysis details of an accepted review
@app.route("/analysis/<int:review_id>")
def analysis(review_id):
    review = Review.query.get_or_404(review_id)
    return render_template("analysis.html", review=review)

if __name__ == "__main__":
    app.run(debug=True)
