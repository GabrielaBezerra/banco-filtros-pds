# Script de busca pelos melhores valores de frequência de corte e ordem do banco de filtros

import time
import matplotlib.pyplot as plt
import numpy as np
import scipy.io
from scipy import signal
import sounddevice as sd
import csv

# --- Passo 1: Carregar o arquivo .mat ---
mat_data = scipy.io.loadmat('voz_int.mat')

sinal_original = mat_data['z'].flatten()
frequencia_amostragem = 12000

# --- Passo 2: Analisar o espectro do sinal original ---
tamanho_sinal_original = len(sinal_original)
frequencias_original = np.fft.fftfreq(tamanho_sinal_original, d=1/frequencia_amostragem)
espectro_original = np.fft.fft(sinal_original)

# --- Funções auxiliares ---
def aplicar_filtros_passa_baixa(sinal, fs, lowcut, ordem):
    # Filtro passa-baixa
    coeficientes_passa_baixa_b, coeficientes_passa_baixa_a = signal.butter(
        ordem, lowcut / (fs / 2), btype='low'
    )
    sinal_filtrado_passa_baixa = signal.lfilter(
        coeficientes_passa_baixa_b, coeficientes_passa_baixa_a, sinal
    )
    return sinal_filtrado_passa_baixa

def aplicar_filtros_passa_banda(sinal, fs, bandcut, ordem):
    # Filtro passa-banda
    coeficientes_passa_banda_b, coeficientes_passa_banda_a = signal.butter(
        ordem, [bandcut[0] / (fs / 2), bandcut[1] / (fs / 2)], btype='bandpass'
    )
    sinal_filtrado_passa_banda = signal.lfilter(
        coeficientes_passa_banda_b, coeficientes_passa_banda_a, sinal
    )
    return sinal_filtrado_passa_banda

def aplicar_filtros_passa_alta(sinal, fs, highcut, ordem):
    # Filtro passa-alta
    coeficientes_passa_alta_b, coeficientes_passa_alta_a = signal.butter(
        ordem, highcut / (fs / 2), btype='high'
    )
    sinal_filtrado_passa_alta = signal.lfilter(
        coeficientes_passa_alta_b, coeficientes_passa_alta_a, sinal
    )
    return sinal_filtrado_passa_alta

def aplicar_banco_de_filtros(sinal, fs, lowcut, highcut, bandcut, ordem_passa_baixa, ordem_passa_banda, ordem_passa_alta):
    sinal_filtrado_passa_baixa = aplicar_filtros_passa_baixa(sinal, fs, lowcut, ordem_passa_baixa)
    sinal_filtrado_passa_banda = aplicar_filtros_passa_banda(sinal, fs, bandcut, ordem_passa_banda)
    sinal_filtrado_passa_alta = aplicar_filtros_passa_alta(sinal, fs, highcut, ordem_passa_alta)
    
    # Combinar os sinais filtrados
    sinal_final_filtrado = (
        sinal_filtrado_passa_baixa + sinal_filtrado_passa_banda + sinal_filtrado_passa_alta
    )
    return sinal_final_filtrado

def calcular_espectro(sinal, fs):
    freqs = np.fft.fftfreq(len(sinal), d=1/fs)
    spectrum = np.fft.fft(sinal)
    return freqs, spectrum

def valores_atenuados(freqs, spectrum):
    res = np.abs(spectrum)[:len(freqs)//2]
    return (res[7440], res[22320])

def plot_spectrum(sinal, fs, title):
    freqs, spectrum = calcular_espectro(sinal, fs)
    plt.figure()
    plt.plot(freqs[:len(freqs)//2], np.abs(spectrum)[:len(freqs)//2])
    plt.title(title)
    plt.xlabel('Frequência (Hz)')
    plt.ylabel('Magnitude')
    plt.grid()
    plt.show()

# --- Passo 3: Busca em grade para encontrar os melhores parâmetros ---
best_params = None
good_params = []
# target_value = np.float64(146.6460693944266)
target_value = 10
lowest_target_value1 = np.float64('inf')
lowest_target_value2 = np.float64('inf')

ordem_range_passa_baixa = range(10, 40, 1)
ordem_range_passa_banda = range(10, 40, 1)
ordem_range_passa_alta = range(10, 40, 1)

lowcut_range = np.arange(1000, 1200, 25)
highcut_range = np.arange(3800, 4000, 25)
# bandcut_range = [(1400, 3500)]
bandcut_range = []
for start in np.arange(1300, 3700, 25):
    for width in np.arange(2000, 2400, 25):
        end = start + width
        if end <= 3700:
            bandcut_range.append((start, end))

total_ops = len(lowcut_range) * len(highcut_range) * len(bandcut_range) * len(ordem_range_passa_baixa) * len(ordem_range_passa_banda) * len(ordem_range_passa_alta)   
op_count = 0

for lowcut in lowcut_range:
    for highcut in highcut_range:
        for bandcut in bandcut_range:
            for ordem_passa_baixa in ordem_range_passa_baixa:
                for ordem_passa_banda in ordem_range_passa_banda:
                    for ordem_passa_alta in ordem_range_passa_alta:
                        op_count += 1
                        timestamp = time.time()
                        sinal_filtrado = aplicar_banco_de_filtros(
                            sinal_original, frequencia_amostragem, lowcut, highcut, bandcut, ordem_passa_baixa, ordem_passa_banda, ordem_passa_alta
                        )
                        freqs, spectrum = calcular_espectro(sinal_filtrado, frequencia_amostragem)
                        interferencia_1, interferencia_2 = valores_atenuados(freqs, spectrum)
                        if interferencia_1 < target_value and interferencia_2 < target_value:
                            good_params.append((lowcut, highcut, bandcut, ordem_passa_baixa, ordem_passa_banda, ordem_passa_alta, interferencia_1, interferencia_2))
                            if lowest_target_value1 > interferencia_1 and lowest_target_value2 > interferencia_2:
                                best_params = (lowcut, highcut, bandcut, ordem_passa_baixa, ordem_passa_banda, ordem_passa_alta)
                        print(f"Progresso: {op_count}/{total_ops} ({op_count/total_ops*100:.2f}%) - Tempo restante estimado: {time.strftime('%H:%M:%S', time.gmtime(0.01 * (total_ops - op_count)))}", end='\r')

if best_params:
    print(f"Melhores parâmetros encontrados: Lowcut={best_params[0]}, Highcut={best_params[1]}, Bandcut={best_params[2]}, Ordem_Passa_Baixa={best_params[3]}, Ordem_Passa_Banda={best_params[4]}, Ordem_Passa_Alta={best_params[5]}")
else:
    print("Não foram encontrados parâmetros que atendem ao critério.")

# --- Passo 4: Aplicar os melhores filtros ao sinal original ---
if best_params:
    lowcut, highcut, bandcut, ordem_passa_baixa, ordem_passa_banda, ordem_passa_alta = best_params
    sinal_final_filtrado = aplicar_banco_de_filtros(sinal_original, frequencia_amostragem, lowcut, highcut, bandcut, ordem_passa_baixa, ordem_passa_banda, ordem_passa_alta)

    # Reproduzir o áudio original
    print("Reproduzindo áudio original...")
    sd.play(sinal_original, frequencia_amostragem)
    sd.wait()

    # Reproduzir o áudio filtrado
    print("Reproduzindo áudio filtrado...")
    sd.play(sinal_final_filtrado, frequencia_amostragem)
    sd.wait()

    # Plotar o espectro de frequência do sinal filtrado
    plot_spectrum(sinal_original, frequencia_amostragem, 'Espectro de Frequência - Sinal Original')
    plot_spectrum(sinal_final_filtrado, frequencia_amostragem, 'Espectro de Frequência - Sinal Filtrado')
else:
    print("Não foi possível aplicar os filtros, pois não foram encontrados parâmetros válidos.")

# --- Passo 5: Salvar os resultados good_params em um csv
with open(f'good_params-{time.time()}.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Lowcut', 'Highcut', 'Bandcut', 'Ordem_Passa_Baixa', 'Ordem_Passa_Banda', 'Ordem_Passa_Alta', 'Atenuacao_1', 'Atenuacao_2'])
    for params in good_params:
        writer.writerow(params)