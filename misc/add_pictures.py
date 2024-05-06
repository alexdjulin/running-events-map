import os

pictures_path = r'C:\Users\natha\Pictures\osee'
folder = os.path.basename(pictures_path)
print(folder)

html_content = '<div style="text-align: center;">\n'

for pic in os.listdir(pictures_path):
	print(pic)
	if pic.lower()[-4:] in {'.jpg', '.png'}:
		html_content += f'<a href="https://alexdjulin.ovh/run/blog/{folder}/{pic}"><img alt="image" src="https://alexdjulin.ovh/run/blog/{folder}/{pic}" /></a>\n'

html_content += '</div>'

file_path = f"{folder}_pictures.html"  # Replace with the desired file path

# Open the file in write mode
with open(file_path, "w") as file:
    file.write(html_content)

print(f"HTML content has been saved to {file_path}")