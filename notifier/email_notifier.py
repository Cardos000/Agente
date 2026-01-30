import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from config import SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT

class EmailNotifier:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def send_report(self, listings):
        if not listings:
            self.logger.info("No new listings to send.")
            return

        if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECIPIENT:
            self.logger.warning("Email credentials not set. Skipping email.")
            return

        subject = f"Imobiliario Bot: {len(listings)} Novos Apartamentos T2 Encontrados"
        
        # Build HTML
        html_content = """
        <html>
        <head>
            <style>
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .price { color: #d9534f; font-weight: bold; }
                .link { background-color: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; }
            </style>
        </head>
        <body>
            <h2>Novos Apartamentos T2 (< 240k, > 90m2)</h2>
            <table>
                <tr>
                    <th>Portal</th>
                    <th>Titulo</th>
                    <th>Preco</th>
                    <th>Localizacao</th>
                    <th>Link</th>
                </tr>
        """
        
        for item in listings:
            row = f"""
            <tr>
                <td>{item.get('portal', 'N/A')}</td>
                <td>{item.get('title', 'N/A')}</td>
                <td class="price">{item.get('price', 'N/A')} €</td>
                <td>{item.get('location', 'N/A')}</td>
                <td><a href="{item.get('link', '#')}" class="link">Ver Anuncio</a></td>
            </tr>
            """
            html_content += row
            
        html_content += """
            </table>
            <p>Este relatorio foi gerado automaticamente.</p>
        </body>
        </html>
        """

        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_SENDER
            msg['To'] = EMAIL_RECIPIENT
            msg['Subject'] = subject
            msg.attach(MIMEText(html_content, 'html'))

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            self.logger.info(f"Email sent to {EMAIL_RECIPIENT}")
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
