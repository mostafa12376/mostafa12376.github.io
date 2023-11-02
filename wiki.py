import json

# Create a list of posts
posts = []

# Create a function to add a new post
def add_post(title, content):
    post = {
        "title": title,
        "content": content,
        "comments": []
    }
    posts.append(post)

# Create a function to add a new comment to a post
def add_comment(post_id, comment):
    post = posts[post_id]
    post["comments"].append(comment)

# Handle GET requests
def get_posts():
    return json.dumps(posts)

def get_post(post_id):
    post = posts[post_id]
    return json.dumps(post)

# Handle POST requests
def add_post_handler(request):
    title = request.args.get("title")
    content = request.args.get("content")

    add_post(title, content)

    return "Post added successfully!"

def add_comment_handler(request):
    post_id = int(request.args.get("post_id"))
    comment = request.args.get("comment")

    add_comment(post_id, comment)

    return "Comment added successfully!"

# Start the server
if __name__ == "__main__":
    from flask import Flask, request

    app = Flask(__name__)

    # Register GET routes
    app.route("/posts", methods=["GET"])(get_posts)
    app.route("/posts/<int:post_id>", methods=["GET"])(get_post)

    # Register POST routes
    app.route("/posts", methods=["POST"])(add_post_handler)
    app.route("/posts/<int:post_id>/comments", methods=["POST"])(add_comment_handler)

    app.run(debug=True)
