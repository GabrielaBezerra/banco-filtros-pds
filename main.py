import matplotlib.pyplot as plt
import numpy as np
import scipy.io
from scipy import signal
import sounddevice as sd
import soundfile as sf
from scipy.io.wavfile import write

# --- Passo 1: Carregar o arquivo .mat ---
mat_data = scipy.io.loadmat('voz_int.mat')

sinal_original = mat_data['z'].flatten()
print("Frequência de amostragem extraída do sinal:", mat_data['fs'][0][0])
print("Sinal para debug:", mat_data)
frequencia_amostragem = mat_data['fs'][0][0] # Frequência de amostragem (12 kHz)

# --- Passo 2: Analisar o espectro do sinal original ---
# Calcular a FFT (Transformada Rápida de Fourier) para visualizar as frequências presentes no sinal
tamanho_sinal_original = len(sinal_original)
frequencias_original = np.fft.fftfreq(tamanho_sinal_original, d=1/frequencia_amostragem)
espectro_original = np.fft.fft(sinal_original)

# --- Passo 3: Projetar os filtros ---
# Definir frequências de corte normalizadas
ordem_filtro_passa_baixa = 21
frequencia_corte_passa_baixa = 1000 / (frequencia_amostragem / 2)

ordem_filtro_passa_alta = 32
frequencia_corte_passa_alta = 4000 / (frequencia_amostragem / 2)

ordem_filtro_passa_banda = 23
frequencias_corte_passa_banda = [1450 / (frequencia_amostragem / 2),
                                 3550 / (frequencia_amostragem / 2)]

# Filtro passa-baixa (deixa passar frequências abaixo de 1250 Hz)
coeficientes_passa_baixa_b, coeficientes_passa_baixa_a = signal.butter(
    ordem_filtro_passa_baixa, frequencia_corte_passa_baixa, btype='low'
)

# Filtro passa-alta (deixa passar frequências acima de 3750 Hz)
coeficientes_passa_alta_b, coeficientes_passa_alta_a = signal.butter(
    ordem_filtro_passa_alta, frequencia_corte_passa_alta, btype='high'
)

# Filtro passa-banda (deixa passar frequências entre 1250 Hz e 3750 Hz)
coeficientes_passa_banda_b, coeficientes_passa_banda_a = signal.butter(
    ordem_filtro_passa_banda, frequencias_corte_passa_banda, btype='bandpass'
)

# --- Passo 4: Aplicar os filtros ao sinal original ---

# Aplicar o filtro passa-baixa
sinal_filtrado_passa_baixa = signal.lfilter(
    coeficientes_passa_baixa_b, coeficientes_passa_baixa_a, sinal_original
)

# Aplicar o filtro passa-banda
sinal_filtrado_passa_banda = signal.lfilter(
    coeficientes_passa_banda_b, coeficientes_passa_banda_a, sinal_original
)

# Aplicar o filtro passa-alta
sinal_filtrado_passa_alta = signal.lfilter(
    coeficientes_passa_alta_b, coeficientes_passa_alta_a, sinal_original
)

# Combinar os sinais filtrados para obter o sinal final filtrado
sinal_final_filtrado = (
    sinal_filtrado_passa_baixa + sinal_filtrado_passa_banda + sinal_filtrado_passa_alta
)

# --- Passo 6: Mostrar os resultados ---

# Reproduzir o áudio original
# print("Reproduzindo áudio original...")
# sd.play(sinal_original, frequencia_amostragem)
# sd.wait()

# Reproduzir o áudio filtrado
print("Reproduzindo áudio filtrado...")
sd.play(sinal_final_filtrado, frequencia_amostragem)
sd.wait()

# Salvar o áudio filtrado em um arquivo WAV
sf.write('resultados/voz_filtrado.wav', sinal_final_filtrado, frequencia_amostragem)

# Diagrama de polos e zeros de cada filtro
def plot_pz(b, a, title):
    z, p, k = signal.tf2zpk(b, a)
    plt.figure()
    plt.scatter(np.real(z), np.imag(z), marker='o', facecolors='none', edgecolors='b', label='Zeros')
    plt.scatter(np.real(p), np.imag(p), marker='x', color='r', label='Polos')
    plt.title(title)
    plt.xlabel('Real')
    plt.ylabel('Imaginário')
    plt.grid()
    plt.legend()
    plt.show()

plot_pz(coeficientes_passa_baixa_b, coeficientes_passa_baixa_a, 'Diagrama de Polos e Zeros - Filtro Passa-Baixa')
plot_pz(coeficientes_passa_banda_b, coeficientes_passa_banda_a, 'Diagrama de Polos e Zeros - Filtro Passa-Banda')
plot_pz(coeficientes_passa_alta_b, coeficientes_passa_alta_a, 'Diagrama de Polos e Zeros - Filtro Passa-Alta')

# Resposta em frequência do banco de filtros
# def plot_freq_response(b, a, title):
#     w, h = signal.freqz(b, a, worN=8000)
#     plt.figure()
#     plt.plot(0.5 * frequencia_amostragem * w / np.pi, np.abs(h), 'b')
#     plt.title(title)
#     plt.xlabel('Frequency (Hz)')
#     plt.ylabel('Gain')
#     plt.grid()
#     plt.show()

# plot_freq_response(coeficientes_passa_baixa_b, coeficientes_passa_baixa_a, 'Resposta em Frequência - Filtro Passa-Baixa')
# plot_freq_response(coeficientes_passa_banda_b, coeficientes_passa_banda_a, 'Resposta em Frequência - Filtro Passa-Banda')
# plot_freq_response(coeficientes_passa_alta_b, coeficientes_passa_alta_a, 'Resposta em Frequência - Filtro Passa-Alta')

# Resposta em frequência do banco de filtros em um único gráfico
def plot_combined_freq_response():
    plt.figure()
    
    # Filtro Passa-Baixa
    w, h = signal.freqz(coeficientes_passa_baixa_b, coeficientes_passa_baixa_a)
    plt.plot(0.5 * frequencia_amostragem * w / np.pi, np.abs(h), 'b', label='Passa-Baixa')
    
    # Filtro Passa-Banda
    w, h = signal.freqz(coeficientes_passa_banda_b, coeficientes_passa_banda_a)
    plt.plot(0.5 * frequencia_amostragem * w / np.pi, np.abs(h), 'g', label='Passa-Banda')
    
    # Filtro Passa-Alta
    w, h = signal.freqz(coeficientes_passa_alta_b, coeficientes_passa_alta_a)
    plt.plot(0.5 * frequencia_amostragem * w / np.pi, np.abs(h), 'r', label='Passa-Alta')
    
    plt.title('Resposta em Frequência - Banco de Filtros')
    plt.xlabel('Frequência (Hz)')
    plt.ylabel('Ganho')
    plt.grid()
    plt.legend()
    plt.show()

plot_combined_freq_response()

# Espectro de frequência do sinal antes e depois da filtragem
def plot_spectrum(signal, sampling_freq, title):
    freqs = np.fft.fftfreq(len(signal), d=1/sampling_freq)
    spectrum = np.fft.fft(signal)
    plt.figure()
    plt.plot(freqs[:len(freqs)//2], np.abs(spectrum)[:len(freqs)//2])
    plt.title(title)
    plt.xlabel('Frequência (Hz)')
    plt.ylabel('Magnitude')
    plt.grid()
    plt.show()

plot_spectrum(sinal_original, frequencia_amostragem, 'Espectro de Frequência - Sinal Original')
plot_spectrum(sinal_final_filtrado, frequencia_amostragem, 'Espectro de Frequência - Sinal Filtrado')