import os
import imagej
from scyjava import jimport
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
import numpy as np

input_image_path = None
output = None
process_status = False
size_parameter = "5000-Infinity"
scalebar_pixels = None
scalebar_nm = None
preview_photo = None
exclude_edges = False 


def file_handler():
    global input_image_path, preview_photo
    path = filedialog.askopenfilename(
        title="Wybierz plik",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.tif *.tiff"), ("All files", "*.*")]
    )

    if path:
        input_image_path = path
        input_label.config(text=f"{os.path.basename(path)}")
        
        try:
            img = Image.open(path)
            img.thumbnail((600, 600))
            preview_photo = ImageTk.PhotoImage(img)
            preview_label.config(image=preview_photo, text="")
        except Exception as e:
            preview_label.config(text="Błąd wczytywania podglądu", image="")
            print(f"Preview error: {e}")
        
        check_ready()

def choose_output():
    global output
    path = filedialog.askdirectory(
        title="Wybierz, gdzie zapisać wyniki"
    )
    if path:
        output = path
        output_label.config(text=f"{path}")
        check_ready()

def check_ready():
    if input_image_path and output:
        start_button.config(state="normal")
    else:
        start_button.config(state="disabled")

def measure_scalebar_interactive(image_path):
    img_full = cv2.imread(image_path)
    height, width = img_full.shape[:2]
    
    crop_x = int(width * 0.50)
    crop_y = int(height * 0.88)
    
    img = img_full[crop_y:height, crop_x:width].copy()
    
    points = []
    
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 2:
            points.append((x, y))
            cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
            cv2.imshow('Zmierz podziałkę', img)
            
            if len(points) == 2:
                dist = np.sqrt((points[1][0] - points[0][0])**2 + 
                              (points[1][1] - points[0][1])**2)
                print(f"Długość podziałki: {dist:.2f} pikseli")
                cv2.line(img, points[0], points[1], (0, 255, 0), 2)
                cv2.imshow('Zmierz podziałkę', img)
    
    cv2.imshow('Zmierz podziałkę', img)
    cv2.setMouseCallback('Zmierz podziałkę', mouse_callback)
    
    print("Kliknij początek i koniec podziałki w prawym dolnym rogu. Naciśnij ESC aby zakończyć.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    if len(points) == 2:
        distance = np.sqrt((points[1][0] - points[0][0])**2 + 
                          (points[1][1] - points[0][1])**2)
        return distance
    return None

def add_particle_labels(image_path, csv_path, output_path):
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
   
    df = pd.read_csv(csv_path)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except:
        try:
            font = ImageFont.truetype("Arial.ttf", 12)
        except:
            font = ImageFont.load_default()

    for idx, row in df.iterrows():
        if 'X_pixels' in df.columns and 'Y_pixels' in df.columns:
            x = int(row['X_pixels'])
            y = int(row['Y_pixels'])
            label = str(idx + 1)  
            
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
           
            outline_width = 2
          
            for adj_x in range(-outline_width, outline_width + 1):
                for adj_y in range(-outline_width, outline_width + 1):
                    draw.text((x - text_width//2 + adj_x, y - text_height//2 + adj_y), 
                             label, font=font, fill='black')

            draw.text((x - text_width//2, y - text_height//2), 
                     label, font=font, fill='yellow')

    img.save(output_path)
    print(f"Labeled image saved to {output_path}")

def start_process():
    global process_status, size_parameter, scalebar_pixels, scalebar_nm, exclude_edges
    if not input_image_path or not output:
        messagebox.showerror("Błąd", "Proszę wybrać zarówno plik wejściowy, jak i katalog wyjściowy")
        return
    
    size_value = size_entry.get().strip()
    if not size_value:
        messagebox.showerror("Błąd", "Proszę podać parametr rozmiaru")
        return
    
    size_parameter = size_value
    exclude_edges = exclude_edges_var.get()
    
    start_button.config(state="disabled", text="...")
    root.update()
    
    try:
        scalebar_pixels = measure_scalebar_interactive(input_image_path)
        
        if scalebar_pixels is None:
            messagebox.showerror("Błąd", "Nie zmierzono podziałki")
            start_button.config(state="normal", text="Start")
            return
        
        scalebar_nm = float(simpledialog.askstring("Wartość podziałki", 
                                                  f"Podziałka ma {scalebar_pixels:.2f} pikseli.\nPodaj wartość w nanometrach:"))
        
        if scalebar_nm is None or scalebar_nm <= 0:
            messagebox.showerror("Błąd", "Nieprawidłowa wartość podziałki")
            start_button.config(state="normal", text="Start")
            return
        
        process_images()
        start_button.config(state="normal", text="Start")
        final_images()
    except Exception as e:
        start_button.config(state="normal", text="Start")
        messagebox.showerror("Błąd", f"Wystąpił błąd podczas przetwarzania:\n{e}")

def final_images():
    prefix = os.path.splitext(os.path.basename(input_image_path))[0]

    comparison_window = tk.Toplevel(root)
    comparison_window.title("Zdjęcia końcowe")
    comparison_window.geometry("1400x700")
    frame = ttk.Frame(comparison_window, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)
    
    try:
        input_img = Image.open(input_image_path)
        input_img.thumbnail((580, 550))
        input_photo = ImageTk.PhotoImage(input_img)
        
        input_frame = ttk.LabelFrame(frame, text="Obraz wejściowy", padding="5")
        input_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        input_display = tk.Label(input_frame, image=input_photo)
        input_display.image = input_photo
        input_display.pack()
    except Exception as e:
        print(f"Error loading input image: {e}")
    
    try:
        jpeg_output_path = os.path.join(output, f"{prefix}_wynik_jpg.jpg")
        output_img = Image.open(jpeg_output_path)
        output_img.thumbnail((580, 550))
        output_photo = ImageTk.PhotoImage(output_img)
        
        output_frame = ttk.LabelFrame(frame, text="Obraz wyjściowy", padding="5")
        output_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        output_display = tk.Label(output_frame, image=output_photo)
        output_display.image = output_photo
        output_display.pack()
    except Exception as e:
        print(f"Error loading output image: {e}")
    
    stats_frame = ttk.LabelFrame(frame, text="Statystyki", padding="10")
    stats_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    try:
        stats_csv_path = os.path.join(output, f"{prefix}_wyniki_stat.csv")
        stats_df = pd.read_csv(stats_csv_path)
        
        stats_text = tk.Text(stats_frame, height=12, width=120, font=('Courier', 10))
        stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=stats_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        stats_text.config(yscrollcommand=scrollbar.set)
        
        stats_text.insert(tk.END, "=" * 100 + "\n")
        stats_text.insert(tk.END, "STATYSTYKI ANALIZY\n")
        stats_text.insert(tk.END, "=" * 100 + "\n\n")
        
        for col in stats_df.columns:
            value = stats_df[col].iloc[0]
            stats_text.insert(tk.END, f"{col:.<50} {value:>15.4f}\n")
        
        stats_text.insert(tk.END, "\n" + "=" * 100 + "\n")
        stats_text.config(state=tk.DISABLED)
        
    except Exception as e:
        print(f"Error loading statistics: {e}")
    
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(0, weight=1)
    frame.rowconfigure(1, weight=0)

def process_images():
    global scalebar_pixels, scalebar_nm
    print(f"Plik: {input_image_path}")
    print(f"Miejsce zapisu: {output}")
    
    prefix = os.path.splitext(os.path.basename(input_image_path))[0]
    
    pixels_per_nm = scalebar_pixels / scalebar_nm
    print(f"Skala: {pixels_per_nm:.4f} pikseli/nm")
    
    ij = imagej.init()
    
    Roi = jimport('ij.gui.Roi')
    
    dataset = ij.io().open(input_image_path)
    imp = ij.py.to_imageplus(dataset)
    imp.show()
    
    width = imp.getWidth()
    height = imp.getHeight()
    roi_width = width  
    roi_height = int(height * 0.92)

    roi = Roi(0, 0, roi_width, roi_height)
    imp.setRoi(roi)
    imp.show()
    
    ij.py.run_macro("setBatchMode(true);")
    
    ij.IJ.run(imp, "Crop", "")
    ij.IJ.run(imp, "Enhance Contrast", "saturated=0.55")
    ij.IJ.run(imp, "8-bit", "")
    
    ij.IJ.setAutoThreshold(imp, "Default dark")
    ij.IJ.run(imp, "Convert to Mask", "")
    
    ij.IJ.run(imp, "Fill Holes", "")
    
    ij.IJ.run(imp,"Set Scale...", f"distance={scalebar_pixels} known={scalebar_nm} unit=nm")
  
    ij.IJ.run("Set Measurements...", "area mean perimeter shape feret's integrated centroid display redirect=None decimal=3")
    
    exclude_param = " exclude" if exclude_edges else ""
    ij.IJ.run(imp, "Analyze Particles...", f"size={size_parameter} circularity=0.00-1.00 show=Nothing display clear{exclude_param}")
    
    results_table = ij.ResultsTable.getResultsTable()
    csv_output = os.path.join(output, f"{prefix}_wynik_csv.csv")
    results_table.save(csv_output)
    
    jpeg_no_labels_path = os.path.join(output, f"{prefix}_wynik_bez_etykiet.jpg")
    ij.IJ.saveAs(imp, "Jpeg", jpeg_no_labels_path)
    
    df = pd.read_csv(csv_output)
    
    nm_per_pixel = scalebar_nm / scalebar_pixels
    if 'X' in df.columns and 'Y' in df.columns:
        df['X_pixels'] = df['X'] / nm_per_pixel
        df['Y_pixels'] = df['Y'] / nm_per_pixel
    
    csv_pixel_output_path = os.path.join(output, f"{prefix}_wynik_pixels.csv")
    df.to_csv(csv_pixel_output_path, index=False)
    
    jpeg_output_path = os.path.join(output, f"{prefix}_wynik_jpg.jpg")
    add_particle_labels(jpeg_no_labels_path, csv_pixel_output_path, jpeg_output_path)
    
    print("Koniec.")
    
    df = pd.read_csv(csv_output)
    
    if 'Area' in df.columns:
        df['Radius'] = np.sqrt(df['Area'] / np.pi)
    
    csv_output_with_radius = os.path.join(output, f"{prefix}_wynik_csv.csv")
    df.to_csv(csv_output_with_radius, index=False)
    
    print(f"\nAnalyzed {len(df)} particles")
    print(f"\nDataFrame columns: {df.columns.tolist()}")
    
    stats = {}
    
    if 'Area' in df.columns:
        stats['Średnia powierzchnia (nm²)'] = df['Area'].mean()
        stats['Mediana powierzchni (nm²)'] = df['Area'].median()
        stats['Odchychlenie standardowe powierzchni (nm²)'] = df['Area'].std()
    
    if 'Radius' in df.columns:
        stats['Średni promień (nm)'] = df['Radius'].mean()
        stats['Mediana promienia (nm)'] = df['Radius'].median()
        stats['Odchychlenie standardowe promienia (nm)'] = df['Radius'].std()
    
    if 'Circ.' in df.columns:
        stats['Średnia okrągłość'] = df['Circ.'].mean()
        stats['Mediana okrągłości'] = df['Circ.'].median()
        stats['Odchychlenie standardowe okrągłości'] = df['Circ.'].std()
    elif 'Round' in df.columns:
        stats['Średnia okrągłość'] = df['Round'].mean()
        stats['Mediana okrągłości'] = df['Round'].median()
        stats['Odchychlenie standardowe okrągłości'] = df['Round'].std()
    
    cropped_width = roi_width
    cropped_height = roi_height
    total_area_nm2 = (cropped_width / pixels_per_nm) * (cropped_height / pixels_per_nm)
    total_area_um2 = total_area_nm2 / 1e6
    
    if 'Area' in df.columns:
        total_particle_area = df['Area'].sum()
        coverage_percent = (total_particle_area / total_area_nm2) * 100
        stats['Pokrycie (%)'] = coverage_percent
    
    particle_count = len(df)
    stats['Liczba cząstek'] = particle_count
    stats['Gęstość powierzchniowa (cząstek/μm²)'] = particle_count / total_area_um2
    
    stats_df = pd.DataFrame([stats])
    stats_csv_path = os.path.join(output, f"{prefix}_wyniki_stat.csv")
    stats_df.to_csv(stats_csv_path, index=False)
    print(f"\nStatystyki zapisane do: {stats_csv_path}")
    print("\n=== Statystyki ===")
    for key, value in stats.items():
        print(f"{key}: {value:.4f}")
    
    sns.set_style("whitegrid")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Wyniki analizy', fontsize=24, fontweight='bold')
    
    if 'Radius' in df.columns:
        sns.histplot(data=df, x='Radius', kde=True, bins=30, ax=axes[0, 0], color='skyblue')
        axes[0, 0].set_title('Rozkład promienia cząstek')
        axes[0, 0].set_xlabel('Promień (nm)')
        axes[0, 0].set_ylabel('Ilość')

    if 'Round' in df.columns:
        sns.histplot(data=df, x='Round', kde=True, bins=30, ax=axes[0, 1], color='lightcoral')
        axes[0, 1].set_title('Rozkład okrągłości cząstek')
        axes[0, 1].set_xlabel('Okrągłość')
        axes[0, 1].set_ylabel('Ilość')
    
    if 'Area' in df.columns and 'Perim.' in df.columns:
        sns.scatterplot(data=df, x='Area', y='Perim.', ax=axes[1, 0], color='mediumseagreen', s=50, alpha=0.6)
        axes[1, 0].set_title('Pole powierzchni vs Obwód')
        axes[1, 0].set_xlabel('Pole powierzchni (nm²)')
        axes[1, 0].set_ylabel('Obwód (nm)')

    if 'Feret' in df.columns:
        sns.histplot(data=df, x='Feret', kde=True, bins=30, ax=axes[1, 1], color='plum')
        axes[1, 1].set_title("Rozkład średnicy Fereta")
        axes[1, 1].set_xlabel("Średnica Fereta (nm)")
        axes[1, 1].set_ylabel('Ilość')
    
    plt.tight_layout()
    graphs_output_path = os.path.join(output, f'{prefix}_wykresy.png')
    plt.savefig(graphs_output_path, dpi=300, bbox_inches='tight')
    print(f"\nZapisano jako '{graphs_output_path}'")
    plt.show()
    
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))
    fig2.suptitle('Dodatkowe wykresy', fontsize=16, fontweight='bold')

    if 'Radius' in df.columns and 'Round' in df.columns:
        sns.scatterplot(data=df, x='Radius', y='Round', ax=axes2[0], 
                       hue='Round', palette='viridis', s=60, alpha=0.7, legend=False)
        axes2[0].set_title('Promień vs Okrągłość')
        axes2[0].set_xlabel('Promień (nm)')
        axes2[0].set_ylabel('Okrągłość')

    if 'AR' in df.columns:
        sns.histplot(data=df, x='AR', kde=True, bins=30, ax=axes2[1], color='lightblue')
        axes2[1].set_title('Rozkład współczynnika kształtu')
        axes2[1].set_xlabel('Współczynnik kształtu')
        axes2[1].set_ylabel('Ilość')
    elif 'Round' in df.columns:
        sns.histplot(data=df, x='Round', kde=True, bins=30, ax=axes2[1], color='lightblue')
        axes2[1].set_title('Rozkład okrągłości')
        axes2[1].set_xlabel('Okrągłość')
        axes2[1].set_ylabel('Ilość')
    
    plt.tight_layout()
    additional_graphs_output_path = os.path.join(output, f'{prefix}_wykresy_dodatkowe.png')
    plt.savefig(additional_graphs_output_path, dpi=300, bbox_inches='tight')
    print(f"Zapisano jako '{additional_graphs_output_path}'")
    plt.show()

    print(df.describe())

root = tk.Tk()
root.title("Analiza obrazu SEM")
root.geometry("1200x800")
root.resizable(True, True)

main_frame = ttk.Frame(root, padding="20")
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

title_label = ttk.Label(main_frame, text="Analiza Obrazu SEM", font=("Helvetica", 14, "bold"))
title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=(tk.W, tk.E))


input_button = ttk.Button(main_frame, text="Wybierz plik wejściowy", command=file_handler)
input_button.grid(row=1, column=0, pady=10, padx=5, sticky=(tk.W, tk.E))

input_label = ttk.Label(main_frame, text="Nie wybrano pliku", foreground="gray")
input_label.grid(row=1, column=1, pady=10, padx=5, sticky=(tk.W, tk.E))

output_button = ttk.Button(main_frame, text="Wybierz katalog wyjściowy", command=choose_output)
output_button.grid(row=2, column=0, pady=10, padx=5, sticky=(tk.W, tk.E))

output_label = ttk.Label(main_frame, text="Nie wybrano katalogu", foreground="gray")
output_label.grid(row=2, column=1, pady=10, padx=5, sticky=(tk.W, tk.E))

size_label = ttk.Label(main_frame, text="Rozmiar cząstek (nm²):", font=("Helvetica", 10))
size_label.grid(row=3, column=0, pady=10, padx=5, sticky=tk.W)

size_entry = ttk.Entry(main_frame, width=30)
size_entry.insert(0, "5000-Infinity")
size_entry.grid(row=3, column=1, pady=10, padx=5, sticky=(tk.W, tk.E))

size_info = ttk.Label(main_frame, text="(np. 5000-Infinity, 3000-10000, itp.)", foreground="gray", font=("Helvetica", 8))
size_info.grid(row=4, column=1, pady=(0, 10), padx=5, sticky=(tk.W, tk.E))

exclude_edges_var = tk.BooleanVar(value=False)
exclude_edges_checkbox = ttk.Checkbutton(main_frame, text="Wyklucz cząstki na krawędziach", variable=exclude_edges_var)
exclude_edges_checkbox.grid(row=5, column=0, columnspan=2, pady=10, padx=5, sticky=tk.W)

preview_frame = ttk.LabelFrame(main_frame, text="Podgląd obrazu", padding="10")
preview_frame.grid(row=6, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))

preview_label = ttk.Label(preview_frame, text="Brak podglądu", foreground="gray")
preview_label.pack()

start_button = ttk.Button(main_frame, text="Start", command=start_process, state="disabled")
start_button.grid(row=7, column=0, columnspan=2, pady=(30, 0), sticky=(tk.W, tk.E))

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=2)
main_frame.rowconfigure(6, weight=1)

root.mainloop()
