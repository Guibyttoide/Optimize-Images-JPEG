import os
from pathlib import Path
import concurrent.futures
import time
from tqdm import tqdm
from PIL import Image
import sys

def optimize_png(input_path, output_path, max_size_mb=15):
    """
    Otimiza uma imagem PNG reduzindo sua qualidade até atingir o tamanho desejado.
    
    Args:
        input_path (str): Caminho do arquivo PNG original
        output_path (str): Caminho para salvar o arquivo PNG otimizado
        max_size_mb (int): Tamanho máximo desejado em MB
    """
    try:
        # Abre a imagem
        with Image.open(input_path) as img:
            # Converte para RGB se estiver em outro modo
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calcula as dimensões ideais mantendo a proporção
            max_dimension = 4000  # Máximo de 4000 pixels em qualquer dimensão
            width, height = img.size
            if width > max_dimension or height > max_dimension:
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Configurações iniciais de otimização
            quality = 90
            optimize = True
            
            while True:
                # Salva temporariamente para verificar o tamanho
                img.save(output_path, 'JPEG', quality=quality, optimize=optimize)
                
                # Verifica o tamanho do arquivo
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                
                # Se o arquivo está menor que o tamanho máximo ou a qualidade está muito baixa, para
                if size_mb <= max_size_mb or quality < 30:
                    break
                
                # Reduz a qualidade e tenta novamente
                quality -= 5
        
        return True, size_mb
    except Exception as e:
        print(f"Erro ao otimizar {input_path}: {str(e)}")
        return False, 0

def process_directory(input_dir, output_dir, max_workers=4, max_size_mb=15):
    """
    Processa todos os arquivos PNG em um diretório.
    
    Args:
        input_dir (str): Diretório com os arquivos PNG
        output_dir (str): Diretório para salvar os arquivos otimizados
        max_workers (int): Número máximo de threads para processamento paralelo
        max_size_mb (int): Tamanho máximo desejado para cada imagem em MB
    """
    # Cria o diretório de saída se não existir
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Lista todos os arquivos PNG
    png_files = list(Path(input_dir).glob('**/*.png'))
    
    if not png_files:
        print("Nenhum arquivo PNG encontrado!")
        return
    
    print(f"Encontrados {len(png_files)} arquivos PNG")
    
    # Estatísticas
    total_original_size = 0
    total_optimized_size = 0
    
    # Prepara as tarefas de otimização
    optimization_tasks = []
    for png_path in png_files:
        # Mantém a estrutura de diretórios relativa
        relative_path = png_path.relative_to(input_dir)
        output_path = Path(output_dir) / relative_path.with_suffix('.jpg')
        
        # Cria os subdiretórios necessários
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Adiciona à lista de tarefas
        optimization_tasks.append((str(png_path), str(output_path)))
        total_original_size += os.path.getsize(png_path) / (1024 * 1024)
    
    # Processa as otimizações em paralelo com barra de progresso
    successful = 0
    failed = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(optimize_png, input_path, output_path, max_size_mb): 
                  (input_path, output_path) for input_path, output_path in optimization_tasks}
        
        with tqdm(total=len(optimization_tasks), desc="Otimizando imagens") as pbar:
            for future in concurrent.futures.as_completed(futures):
                success, size_mb = future.result()
                if success:
                    successful += 1
                    total_optimized_size += size_mb
                else:
                    failed += 1
                pbar.update(1)
    
    # Exibe relatório final
    print(f"\nOtimização concluída!")
    print(f"Convertidas com sucesso: {successful}")
    print(f"Falhas na conversão: {failed}")
    print(f"\nTamanho total original: {total_original_size:.2f} MB")
    print(f"Tamanho total otimizado: {total_optimized_size:.2f} MB")
    print(f"Redução total: {((total_original_size - total_optimized_size) / total_original_size * 100):.2f}%")

if __name__ == "__main__":
    # Configurações
    INPUT_DIR = r"C:\Users\Guilherme-PC\Desktop\Convertido"  # Diretório com as imagens PNG
    OUTPUT_DIR = r"C:\Users\Guilherme-PC\Desktop\Otimizado"  # Diretório para salvar as imagens otimizadas
    MAX_WORKERS = 14  # Número de threads para processamento paralelo
    MAX_SIZE_MB = 15  # Tamanho máximo desejado para cada imagem em MB
    
    # Registra o tempo de início
    start_time = time.time()
    
    # Executa o processamento
    process_directory(INPUT_DIR, OUTPUT_DIR, MAX_WORKERS, MAX_SIZE_MB)
    
    # Calcula e exibe o tempo total
    elapsed_time = time.time() - start_time
    print(f"\nTempo total de processamento: {elapsed_time:.2f} segundos")