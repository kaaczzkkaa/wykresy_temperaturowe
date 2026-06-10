# -*- coding: utf-8 -*-
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button, RadioButtons
import tkinter as tk
from tkinter import filedialog

# --- FUNKCJA DO WCZYTYWANIA I PRZETWARZANIA DANYCH ---
def wczytaj_dane_csv(sciezka_pliku):
    t_axis = []
    points = { 'T1': [], 'T2': [], 'T3': [], 'T4': [] }
    
    try:
        with open(sciezka_pliku, mode='r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        print(f"Odczytano surowych linii z pliku: {len(lines)}")
        first_timestamp = None
        
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            row = line.split(';') if ';' in line else line.split(',')
                
            if len(row) < 3 or not row[0].strip().startswith('202'):
                continue
                
            try:
                date_str = row[0].strip()
                time_str = row[1].strip()
                full_datetime_str = f"{date_str} {time_str}".replace('-', '/')
                current_time = datetime.strptime(full_datetime_str, "%Y/%m/%d %H:%M:%S")
                
                if first_timestamp is None:
                    first_timestamp = current_time
                    
                elapsed_seconds = (current_time - first_timestamp).total_seconds()
                
                def clean_temp(val):
                    val = val.strip().replace('(', '').replace(')', '')
                    if not val or val == '-' or 'null' in val.lower():
                        return None
                    try:
                        return float(val)
                    except ValueError:
                        return None

                t1 = clean_temp(row[2]) if len(row) > 2 else None
                t2 = clean_temp(row[4]) if len(row) > 4 else None
                t3 = clean_temp(row[6]) if len(row) > 6 else None
                t4 = clean_temp(row[8]) if len(row) > 8 else None
                
                t_axis.append(elapsed_seconds)
                points['T1'].append(t1)
                points['T2'].append(t2)
                points['T3'].append(t3)
                points['T4'].append(t4)
                
            except Exception:
                continue
        return t_axis, points
    except Exception as e:
        print(f"Blad podczas odczytu pliku: {e}")
        return None, None

# --- OKNO WYBORU PIERWSZEGO PLIKU ---
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)

print("Oczekiwanie na wybor pliku przez uzytkownika...")
CSV_FILE = filedialog.askopenfilename(
    title="Wybierz plik z pomiaru UT325F (CSV)",
    filetypes=[("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")]
)

if not CSV_FILE:
    print("Anulowano wybor pliku. Zamykanie programu.")
    os._exit(0)

time_axis, wykresy_points = wczytaj_dane_csv(CSV_FILE)

if not time_axis:
    print("Brak prawidlowych danych. Zamykanie programu.")
    os._exit(0)

# --- INICJALIZACJA WYKRESU MATPLOTLIB ---
fig = plt.figure(figsize=(15, 8))
ax = plt.axes([0.06, 0.1, 0.74, 0.8])

# Zmienne globalne steruj¹ce stanem aplikacji
dynamic_elements = []
wybrany_czujnik = 'T1'

def odswiez_wykres_bazowy():
    ax.clear()
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_title("PROFIL TEMPERATUROWY", fontsize=12, fontweight='bold')
    ax.set_xlabel("Czas (Sekundy)", fontsize=10)
    ax.set_ylabel("Temperatura (C)", fontsize=10)
    
    if any(v is not None for v in wykresy_points['T1']): ax.plot(time_axis, wykresy_points['T1'], label='T1', color='darkred', linewidth=2)
    if any(v is not None for v in wykresy_points['T2']): ax.plot(time_axis, wykresy_points['T2'], label='T2', color='darkblue', linewidth=1.5)
    if any(v is not None for v in wykresy_points['T3']): ax.plot(time_axis, wykresy_points['T3'], label='T3', color='darkgreen', linewidth=2)
    if any(v is not None for v in wykresy_points['T4']): ax.plot(time_axis, wykresy_points['T4'], label='T4', color='orange', linewidth=1.5)
    
    ax.legend(loc="upper left")
    ax.relim()
    ax.autoscale_view()

odswiez_wykres_bazowy()

# --- INTERFEJS U¯YTKOWNIKA (PANEL BOCZNY) ---
# Pola tekstowe temperatur
ax_box1 = plt.axes([0.86, 0.80, 0.08, 0.04])
ax_box2 = plt.axes([0.86, 0.70, 0.08, 0.04])
ax_box3 = plt.axes([0.86, 0.60, 0.08, 0.04])

plt.text(0.86, 0.85, "Prog Temp 1 (C):", transform=fig.transFigure, fontweight='bold', fontsize=9)
plt.text(0.86, 0.75, "Prog Temp 2 (C):", transform=fig.transFigure, fontweight='bold', fontsize=9)
plt.text(0.86, 0.65, "Prog Temp 3 (C):", transform=fig.transFigure, fontweight='bold', fontsize=9)

box1 = TextBox(ax_box1, '')
box2 = TextBox(ax_box2, '')
box3 = TextBox(ax_box3, '')

# Prze³¹cznik wyboru krzywej czujnika (RadioButtons)
plt.text(0.86, 0.53, "Mierz zakres dla:", transform=fig.transFigure, fontweight='bold', fontsize=9)
ax_radio = plt.axes([0.86, 0.36, 0.08, 0.15], facecolor='lightgray')
radio_czujniki = RadioButtons(ax_radio, ('T1', 'T2', 'T3', 'T4'), active=0)

# Przycisk wyboru nowego pliku CSV
ax_btn = plt.axes([0.86, 0.20, 0.10, 0.05])
btn_nowy_plik = Button(ax_btn, 'Wybierz inny plik', color='lightblue', hovercolor='skyblue')

# --- NOWA POPRAWIONA LOGIKA PRZELICZANIA ZAKRESÓW ---
def przelicz_zakresy(tekst_wymagany_przez_matplot=None):
    global dynamic_elements, wybrany_czujnik
    
    # Usuniêcie starych linii rysowanych na wykresie
    for elem in dynamic_elements:
        try:
            elem.remove()
        except Exception:
            pass
    dynamic_elements.clear()
    
    # Odczyt danych z aktywnych pól tekstowych
    progi = []
    for b in [box1, box2, box3]:
        t_str = b.text.strip()
        if t_str:
            try:
                progi.append(float(t_str))
            except ValueError:
                pass
                
    if not progi:
        fig.canvas.draw_idle()
        return

    progi.sort()
    strefy_czasowe = {}
    
    # U¿ywamy wybranej przez u¿ytkownika krzywej T1, T2, T3 lub T4
    reference_points = wykresy_points[wybrany_czujnik]
    
    # Sprawdzamy czy wybrany czujnik posiada dane
    if not any(v is not None for v in reference_points):
        print(f"Ostrzezenie: Brak danych pomiarowych dla czujnika {wybrany_czujnik}!")
        fig.canvas.draw_idle()
        return

    # KROK 1: Absolutny pocz¹tek i ostateczny koniec przekroczenia temperatur
    for p in progi:
        t_start = None
        t_end = None
        
        for t, temp in zip(time_axis, reference_points):
            if temp is not None and temp >= p:
                t_start = t
                break
                
        for t, temp in reversed(list(zip(time_axis, reference_points))):
            if temp is not None and temp >= p:
                t_end = t
                break
                
        if t_start is not None and t_end is not None and t_end > t_start:
            strefy_czasowe[p] = [t_start, t_end]

    # KROK 2: Przycinanie zakresów chronologicznie (wy¿szy priorytet wy¿szej temperatury)
    progi_od_najwyzszego = sorted(list(strefy_czasowe.keys()), reverse=True)
    for i, p_wyzszy in enumerate(progi_od_najwyzszego):
        start_wyzszy, end_wyzszy = strefy_czasowe[p_wyzszy]
        for p_nizszy in progi_od_najwyzszego[i+1:]:
            start_nizszy, end_nizszy = strefy_czasowe[p_nizszy]
            if start_wyzszy > start_nizszy and start_wyzszy < end_nizszy:
                strefy_czasowe[p_nizszy][1] = start_wyzszy

    # KROK 3: Rysowanie stref
    colors = ['purple', 'crimson', 'teal']
    for idx, prog in enumerate(progi):
        if prog not in strefy_czasowe:
            continue
            
        start, end = strefy_czasowe[prog]
        dur = round(end - start, 1)
        if dur <= 0:
            continue
            
        kolor = colors[idx % len(colors)]
        
        l1 = ax.axvline(x=start, color=kolor, linestyle='--', alpha=0.7, linewidth=1.2)
        l2 = ax.axvline(x=end, color=kolor, linestyle='--', alpha=0.7, linewidth=1.2)
        span = ax.axvspan(start, end, color=kolor, alpha=0.08)
        dynamic_elements.extend([l1, l2, span])
        
        y_pos = ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * (0.04 + (idx * 0.08))
        srodek_strefy = start + (end - start) / 2
        
        txt = ax.text(srodek_strefy, y_pos, 
                      f"Prog: {prog}C ({wybrany_czujnik})\n{round(start,1)}s - {round(end,1)}s\nCzas: {dur}s", 
                      color=kolor, fontweight='bold', fontsize=8, ha='center',
                      bbox=dict(facecolor='white', alpha=0.85, edgecolor='none'))
        dynamic_elements.append(txt)
            
    fig.canvas.draw_idle()

# --- FUNKCJA ZMIANY CZUJNIKA ---
def zmiana_czujnika(label):
    global wybrany_czujnik
    wybrany_czujnik = label
    print(f"Zmieniono czujnik pomiarowy na: {wybrany_czujnik}")
    przelicz_zakresy() # Automatyczne przeliczenie stref dla nowego czujnika

# --- FUNKCJA WGRANIA NOWEGO PLIKU CSV ---
def wgraj_nowy_plik(event):
    global time_axis, wykresy_points, dynamic_elements
    print("Otwieranie eksploratora dla nowego pliku...")
    nowy_plik = filedialog.askopenfilename(
        title="Wybierz nowy plik z pomiaru UT325F (CSV)",
        filetypes=[("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")]
    )
    if nowy_plik:
        t_axis, p_points = wczytaj_dane_csv(nowy_plik)
        if t_axis:
            time_axis = t_axis
            wykresy_points = p_points
            dynamic_elements.clear()
            
            # Resetujemy i przerysowujemy ca³y wykres bazowy pod nowe dane
            odswiez_wykres_bazowy()
            # Jeœli w polach tekstowych by³y ju¿ wpisane progi, przelicz je automatycznie dla nowych danych
            przelicz_zakresy()
            print("Pomyslnie zaladowano nowy wykres!")

# --- PODPIÊCIE AKCJI POD ELEMENTY INTERFEJSU ---
box1.on_submit(przelicz_zakresy)
box2.on_submit(przelicz_zakresy)
box3.on_submit(przelicz_zakresy)

radio_czujniki.on_clicked(zmiana_czujnika)
btn_nowy_plik.on_clicked(wgraj_nowy_plik)

print("Rysowanie wykresu...")
plt.show()
os._exit(0)