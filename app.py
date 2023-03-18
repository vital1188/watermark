import os
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, request, send_from_directory, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'


def add_watermark(image, watermark, position):
    # Make the image and watermark have the same mode
    if image.mode != watermark.mode:
        image = image.convert(watermark.mode)

    # Create a transparent layer the same size as the image
    layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    layer.paste(image, (0, 0))
    layer.paste(watermark, position, mask=watermark)

    return layer


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    image = request.files['image']
    watermark = request.files['watermark']
    use_default_logo = request.form.get('use_default_logo')
    text = request.form['text']
    text_color = request.form['text_color']
    position = request.form['position']
    scale = int(request.form['scale'])

    image_filename = secure_filename(image.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    image.save(image_path)
    original_image = Image.open(image_path)

    if watermark or use_default_logo == 'on':
        if use_default_logo == 'on':
            watermark_path = os.path.join('static', 'default_logo.png')
        else:
            watermark_filename = secure_filename(watermark.filename)
            watermark_path = os.path.join(
                app.config['UPLOAD_FOLDER'], watermark_filename)
            watermark.save(watermark_path)

        watermark_image = Image.open(watermark_path)
    elif text:
        watermark_image = Image.new('RGBA', (300, 60), (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark_image)
        font = ImageFont.truetype('arial.ttf', 30)
        draw.text((0, 0), text, font=font, fill=text_color)
    else:
        return "Please provide a watermark image or text."

    # Resize the watermark
    watermark_width = int(watermark_image.width * (scale / 100))
    watermark_height = int(watermark_image.height * (scale / 100))
    watermark_image = watermark_image.resize(
        (watermark_width, watermark_height), Image.ANTIALIAS)

    # Determine the position
    if position == "top-left":
        watermark_position = (0, 0)
    elif position == "top-right":
        watermark_position = (original_image.width - watermark_width, 0)
    elif position == "bottom-left":
        watermark_position = (0, original_image.height - watermark_height)
    elif position == "bottom-right":
        watermark_position = (original_image.width - watermark_width,
                              original_image.height - watermark_height)

    # Add the watermark and save the result
    result = add_watermark(original_image, watermark_image, watermark_position)
    output_filename = f"watermarked_{image_filename}"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    result.save(output_path)

    return send_from_directory(app.config['UPLOAD_FOLDER'], output_filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
