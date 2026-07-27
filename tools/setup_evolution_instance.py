import asyncio
import os
from dotenv import load_dotenv
from app.services.evolution_service import evolution_service
from app.config import settings
import qrcode
from PIL import Image
import io

async def main():
    """
    Cria uma instância no Evolution Go e exibe o QR Code para conexão.
    """
    load_dotenv()

    instance_name = settings.EVOLUTION_INSTANCE_NAME
    if not instance_name:
        print("A variável de ambiente EVOLUTION_INSTANCE_NAME não está definida.")
        return

    print(f"Criando instância '{instance_name}' no Evolution Go...")
    instance_data = await evolution_service.create_instance(instance_name)

    if not instance_data:
        print("Não foi possível criar a instância. Verifique os logs para mais detalhes.")
        return

    print("Instância criada com sucesso. Obtendo QR Code...")
    qr_code_data = await evolution_service.get_qrcode(instance_name)

    if not qr_code_data:
        print("Não foi possível obter o QR Code. Verifique os logs para mais detalhes.")
        return

    print("QR Code obtido com sucesso. Gerando imagem...")

    # Gerar QR Code no terminal
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_code_data.decode('utf-8'))
    qr.make(fit=True)
    
    print("Escaneie o QR Code abaixo com o seu WhatsApp:")
    qr.print_tty()

    # Salvar QR Code como imagem
    img = qr.make_image(fill='black', back_color='white')
    img_path = "qrcode.png"
    img.save(img_path)
    print(f"
QR Code também foi salvo como '{img_path}'.")
    print("Após escanear, a instância estará conectada e pronta para uso.")


if __name__ == "__main__":
    asyncio.run(main())
