import requests
import os
import sys # Added sys
from PIL import Image
import shutil
import re
import subprocess

def get_base_path():
    """Returns the directory to save data. Uses ~/Documents/WeebCentral/"""
    base = os.path.expanduser("~/Documents/WeebCentral")
    os.makedirs(base, exist_ok=True)
    return base

# Headers to mimic a browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'HX-Request': 'true',
}

def get_manga_slug(url):
    """Extracts the manga slug from the series URL."""
    return url.strip('/').split('/')[-1]

def get_series_info(series_url):
    """
    Fetches the series page and the full chapter list.
    Returns a list of tuples: (chapter_number, chapter_id)
    """
    print(f"Fetching series info from: {series_url}")
    
    # 1. Fetch Series Page to get the Series ID (if needed) or just to validate
    # Actually, we can try to hit the full chapter list endpoint directly if we have the series ID from the URL.
    # URL format: https://weebcentral.com/series/SERIES_ID/SLUG
    
    try:
        series_id = series_url.split('/series/')[1].split('/')[0]
    except IndexError:
        print("Invalid URL format. Expected .../series/SERIES_ID/SLUG")
        return []

    full_list_url = f"https://weebcentral.com/series/{series_id}/full-chapter-list"
    print(f"Fetching full chapter list from: {full_list_url}")
    
    response = requests.get(full_list_url, headers={'User-Agent': HEADERS['User-Agent']})
    
    if response.status_code != 200:
        print(f"Failed to fetch chapter list. Status: {response.status_code}")
        return []
    
    # Parse HTML to find chapter links
    # Links look like: <a href="https://weebcentral.com/chapters/CHAPTER_ID" ...>
    # And inside usually contain "Chapter X"
    
    chapter_data = []
    
    # Simple regex to find links and chapter numbers. 
    # This might need refinement based on exact HTML structure, but let's try a robust pattern.
    # We look for the href and then the text content.
    
    # Pattern to find the chapter link and the "Chapter X" text
    # The HTML dump showed: <a href=".../chapters/ID" ...> ... <span ...>Chapter 85</span> ... </a>
    
    # Let's split by "href=" to iterate through links
    parts = response.text.split('href="')
    for part in parts:
        if part.startswith('https://weebcentral.com/chapters/') or part.startswith('/chapters/'):
            # Extract ID
            link_url = part.split('"')[0]
            chapter_id = link_url.split('/')[-1]
            
            # Now look for "Chapter X" in the rest of this 'part' (until the next </a> or similar)
            # This is a bit "loose" parsing but often more robust than strict regex against complex HTML
            # We limit the search window to avoid false positives from far away text
            # Increased to 10000 because inline SVGs can be very large
            search_window = part[:10000] 
            
            chapter_match = re.search(r'(?:Chapter|Episode)\s+(\d+(\.\d+)?)', search_window)
            if chapter_match:
                chapter_num = float(chapter_match.group(1))
                chapter_data.append((chapter_num, chapter_id))
    
    # Sort by chapter number
    chapter_data.sort(key=lambda x: x[0])
    
    print(f"Found {len(chapter_data)} chapters.")
    return chapter_data

def get_chapter_images(chapter_id):
    """
    Fetches image URLs for a chapter using the HTMX endpoint.
    """
    url = f"https://weebcentral.com/chapters/{chapter_id}/images?is_prev=False&current_page=1&reading_style=long_strip"
    # We need the Referer header usually for these HTMX requests
    headers = HEADERS.copy()
    headers['Referer'] = f"https://weebcentral.com/chapters/{chapter_id}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch images for chapter {chapter_id}. Status: {response.status_code}")
        return []
    
    # Extract image URLs
    # They are in <img src="..."> tags
    image_urls = re.findall(r'src="([^"]*)"', response.text)
    
    # Filter for likely manga images (scans.lastation.us, official.lowee.us, etc.)
    # Or just return all valid URLs that look like images if specific domains fail
    valid_images = [img for img in image_urls if 'scans.lastation.us' in img or 'official.lowee.us' in img or 'temp.compsci88.com' in img]
    
    # If strict filtering fails, try a broader filter (e.g. ends with .png, .jpg, .webp)
    if not valid_images:
         valid_images = [img for img in image_urls if img.endswith(('.png', '.jpg', '.jpeg', '.webp')) and 'static/images' not in img]

    return valid_images

def download_image(img_url, save_path):
    """Downloads a single image."""
    try:
        response = requests.get(img_url, headers={'User-Agent': HEADERS['User-Agent']}, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"Error downloading {img_url}: {e}")
    return False

def create_pdf_from_images(image_paths, output_pdf_path):
    """Creates a PDF from a list of image paths."""
    if not image_paths:
        return
    
    images = []
    for img_path in image_paths:
        try:
            img = Image.open(img_path)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            images.append(img)
        except Exception as e:
            print(f"Error processing image {img_path} for PDF: {e}")

    if images:
        images[0].save(output_pdf_path, save_all=True, append_images=images[1:])
        print(f"PDF created: {output_pdf_path}")

def read_manga_list(file_path):
    """Reads the manga list file and returns a list of URLs."""
    urls = []
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                urls.append(line)
    return urls

def process_series(series_url):
    """Processes a single series: checks for new chapters and downloads them."""
    print(f"\n{'='*50}")
    print(f"Processing Series: {series_url}")
    print(f"{'='*50}")
    
    try:
        manga_slug = get_manga_slug(series_url)
        print(f"Manga Name: {manga_slug}")
        
        # Create main manga directory
        os.makedirs(manga_slug, exist_ok=True)
        pdf_folder = os.path.join(manga_slug, "pdfs")
        os.makedirs(pdf_folder, exist_ok=True)
        
        # Get all chapters
        chapters = get_series_info(series_url)
        
        if not chapters:
            print(f"No chapters found for {manga_slug}. Skipping.")
            return

        new_chapters_count = 0
        
        for chapter_num, chapter_id in chapters:
             # Setup strings
            chapter_str = str(chapter_num)
            if chapter_num.is_integer():
                chapter_str = str(int(chapter_num)).zfill(4)
            else:
                 chapter_str = str(chapter_num).zfill(6)

            # Check if PDF already exists
            pdf_path = os.path.join(pdf_folder, f"{manga_slug} - Chapter {chapter_str}.pdf")
            if os.path.exists(pdf_path):
                continue
            
            print(f"Found New/Missing Chapter: {chapter_num}. Downloading...")
            new_chapters_count += 1
            
            # Setup Images Folder
            chapter_folder = os.path.join(manga_slug, "images", f"chapter_{chapter_str}")
            os.makedirs(chapter_folder, exist_ok=True)
            
            # Get Images
            image_urls = get_chapter_images(chapter_id)
            if not image_urls:
                print(f"No images found for Chapter {chapter_num}. Skipping.")
                continue
                
            downloaded_images = []
            for i, img_url in enumerate(image_urls, start=1):
                page_str = str(i).zfill(3)
                img_name = f"{chapter_str}-{page_str}.png" 
                save_path = os.path.join(chapter_folder, img_name)
                
                if download_image(img_url, save_path):
                    downloaded_images.append(save_path)
                else:
                    print(f"Failed to download page {i}")
            
            # Create PDF
            if downloaded_images:
                create_pdf_from_images(downloaded_images, pdf_path)
            else:
                print(f"No images downloaded for Chapter {chapter_num}")

        if new_chapters_count == 0:
            print(f"Up to date. No new chapters for {manga_slug}.")
        else:
            print(f"Downloaded {new_chapters_count} new chapters for {manga_slug}.")

    except Exception as e:
        print(f"Error processing {series_url}: {e}")

def run_scraper_gui(series_url):
    # Add URL to manga_list.txt if not present
    list_file = "manga_list.txt"
    try:
        existing_urls = []
        file_content = ""
        if os.path.exists(list_file):
            with open(list_file, "r") as f:
                file_content = f.read()
                existing_urls = [line.strip() for line in file_content.splitlines() if line.strip()]
        
        if series_url not in existing_urls:
            prefix = ""
            if file_content and not file_content.endswith("\n"):
                prefix = "\n"
                
            with open(list_file, "a") as f:
                f.write(prefix + series_url + "\n")
            print(f"Added {series_url} to {list_file}")
        else:
            print(f"URL already in {list_file}")
    except Exception as e:
        print(f"Failed to update {list_file}: {e}")

    process_series(series_url)
    print("\nDone adding and downloading!")

def run_scraper_mode():
    # Get URL from terminal input
    series_url = input("\nEnter WeebCentral Series URL: ").strip()
    
    if not series_url:
        print("No URL provided. Exiting.")
        return

    # Add URL to manga_list.txt if not present
    list_file = "manga_list.txt"
    try:
        existing_urls = []
        file_content = ""
        if os.path.exists(list_file):
            with open(list_file, "r") as f:
                file_content = f.read()
                existing_urls = [line.strip() for line in file_content.splitlines() if line.strip()]
        
        if series_url not in existing_urls:
            prefix = ""
            if file_content and not file_content.endswith("\n"):
                prefix = "\n"
                
            with open(list_file, "a") as f:
                f.write(prefix + series_url + "\n")
            print(f"Added {series_url} to {list_file}")
        else:
            print(f"URL already in {list_file}")
    except Exception as e:
        print(f"Failed to update {list_file}: {e}")

    process_series(series_url)
    print("\nDone adding and downloading!")

def run_bulk_mode():
    list_file = "manga_list.txt"
    urls = read_manga_list(list_file)
    
    if not urls:
        print("\nNo manga URLs found in manga_list.txt or file is missing.")
        print("Please add WeebCentral series URLs to manga_list.txt, one per line (or use option 1 first).")
        return

    print(f"\nFound {len(urls)} series to check.")
    for url in urls:
        process_series(url)
        
    print("\nBulk update complete!")

def main():
    # Set working directory to the script/exe location
    base_path = get_base_path()
    os.chdir(base_path)

    print("WeebCentral Manager")
    print("-------------------")
    print("1) Add a new manga URL to your list and download it")
    print("2) Update all manga currently in your list")
    
    choice = input("\nEnter 1 or 2: ").strip()
    
    if choice == '1':
        run_scraper_mode()
    elif choice == '2':
        run_bulk_mode()
    else:
        print("Invalid choice. Exiting.")

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
