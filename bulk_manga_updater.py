import os
import sys

# Import functions from the main scraper script
# Ensure the script is in the same directory or PYTHONPATH includes it
try:
    from weebcentral_scraper import (
        get_manga_slug,
        get_series_info,
        get_chapter_images,
        download_image,
        get_series_info,
        get_chapter_images,
        download_image,
        create_pdf_from_images,
        get_base_path
    )
except ImportError:
    print("Error: Could not import 'weebcentral_scraper.py'. Make sure it is in the same directory.")
    sys.exit(1)

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
                # print(f"Chapter {chapter_num} already exists. Skipping.") # Optional: Comment out to reduce noise
                continue
            
            print(f"Found New/Missing Chapter: {chapter_num}. Downloading...")
            new_chapters_count += 1
            
            # Setup Images Folder (Temporary)
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
                # Cleanup images folder to save space (Optional, typically user might want to keep or delete)
                # For now, we leave them as per original script behavior roughly, or we could delete them.
                # The original script didn't delete them.
            else:
                print(f"No images downloaded for Chapter {chapter_num}")

        if new_chapters_count == 0:
            print(f"Up to date. No new chapters for {manga_slug}.")
        else:
            print(f"Downloaded {new_chapters_count} new chapters for {manga_slug}.")

    except Exception as e:
        print(f"Error processing {series_url}: {e}")

def main():
    # Set working directory to the script/exe location
    try:
        base_path = get_base_path()
        os.chdir(base_path)
    except NameError:
        # Fallback if import failed locally
        pass

    list_file = "manga_list.txt"
    urls = read_manga_list(list_file)
    
    if not urls:
        print("No manga URLs found in manga_list.txt or file is missing.")
        print("Please add WeebCentral series URLs to manga_list.txt, one per line.")
        return

    print(f"Found {len(urls)} series to check.")
    
    for url in urls:
        process_series(url)
        
    print("\nBulk update complete!")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
