import yt_dlp as youtube_dl
import subprocess
import re
import os
import argparse
from datetime import timedelta
import glob

def converter_hhmmss_para_segundos(tempo_str):
    h, m, s = tempo_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def main():
    parser = argparse.ArgumentParser(description="Corte vídeos do YouTube")
    parser.add_argument("url", help="URL do vídeo do YouTube")
    parser.add_argument("-s", "--start", default="00:00:00", help="Tempo inicial no formato hh:mm:ss (opcional)")
    parser.add_argument("-e", "--end", default="00:00:00", help="Tempo final no formato hh:mm:ss (opcional)")
    args = parser.parse_args()

    url_do_video = args.url
    tempo_inicio = args.start
    tempo_final = args.end

    # Diretório para salvar os arquivos brutos
    diretorio_brutos = './brutos'
    diretorio_de_download = '.'

    # Cria a pasta "brutos" se ela não existir
    if not os.path.exists(diretorio_brutos):
        os.makedirs(diretorio_brutos)

    # Extrai o valor de tempo de início da URL, se presente
    match = re.search(r'[?&]t=(\d+)', url_do_video)
    if match:
        tempo_inicio_segundos = int(match.group(1))
        tempo_inicio = str(timedelta(seconds=tempo_inicio_segundos))
        print("Usando o tempo inicial por URL")
    else:
        tempo_inicio_segundos = converter_hhmmss_para_segundos(tempo_inicio)

    # Calcula a duração do corte
    if tempo_final != "00:00:00":
        tempo_final_segundos = converter_hhmmss_para_segundos(tempo_final)
        if tempo_final_segundos <= tempo_inicio_segundos:
            raise ValueError("Erro: o tempo final é menor ou igual ao tempo inicial.")
        duracao_corte = tempo_final_segundos - tempo_inicio_segundos
        tempo_final = str(timedelta(seconds=duracao_corte))
    else:
        duracao_corte = None

    print(f"Extraindo informações do vídeo: {url_do_video}")
    # Define as opções para o download
    with youtube_dl.YoutubeDL({'format': 'bestvideo+bestaudio', 'noplaylist': True}) as ydl:
        info_dict = ydl.extract_info(url_do_video, download=False)
        video_title = info_dict.get('title', None)
        print(f"Título do vídeo: {video_title}")
        # Sanitiza o título do vídeo para usar como nome de arquivo
        titulo_sanitizado = re.sub(r'[\\/*?:"<>|]', "", video_title).replace(" ", "_")[:50]
        video_path_pattern = os.path.join(diretorio_brutos, f"{titulo_sanitizado}.*")

    ydl_opts = {
        'format': 'bestvideo+bestaudio',
        'outtmpl': os.path.join(diretorio_brutos, f"{titulo_sanitizado}.%(ext)s")
    }

    if not glob.glob(video_path_pattern):
        print("Baixando vídeo...")
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url_do_video])
        print("Download concluído.")

    # Verifica o nome real do arquivo baixado
    video_path_sanitized = glob.glob(video_path_pattern)[0]
    print(f"Arquivo baixado: {video_path_sanitized}")

    tempo_inicio_str = tempo_inicio.replace(":", "-")
    tempo_final_str = str(timedelta(seconds=tempo_inicio_segundos + duracao_corte)).replace(":", "-") if duracao_corte else "end"
    if duracao_corte:
        final_filename = f"{titulo_sanitizado}_{tempo_inicio_str}_to_{tempo_final_str}.mp4"
    else:
        final_filename = f"{titulo_sanitizado}.mp4"
    final_path = os.path.join(diretorio_de_download, final_filename)

    print(f"Verificando o caminho do arquivo de entrada: {video_path_sanitized}")
    if not os.path.exists(video_path_sanitized):
        raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {video_path_sanitized}")

    # Monta o comando FFmpeg com ou sem a duração do corte
    ffmpeg_command = [
        'ffmpeg', '-ss', tempo_inicio, '-i', video_path_sanitized,
        '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental'
    ]
    if duracao_corte is not None:
        ffmpeg_command += ['-t', tempo_final]
    ffmpeg_command.append(final_path)

    try:
        print("Executando ffmpeg...")
        subprocess.run(ffmpeg_command, check=True)
        print(f'Download, corte (se aplicável) e combinação concluídos: {final_path}')
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o ffmpeg: {e}")

if __name__ == "__main__":
    main()
