from base64 import urlsafe_b64encode
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from py_vapid import Vapid02


class Command(BaseCommand):
    help = 'Génère une paire de clés Web Push VAPID pour Dunia.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--write-env',
            action='store_true',
            help='Écrit les clés dans le .env local sans afficher la clé privée.',
        )

    def handle(self, *args, **options):
        vapid = Vapid02()
        vapid.generate_keys()
        private_key = urlsafe_b64encode(
            vapid.private_key.private_numbers().private_value.to_bytes(32, 'big')
        ).rstrip(b'=').decode('ascii')
        public_key = urlsafe_b64encode(
            vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
        ).rstrip(b'=').decode('ascii')

        if options['write_env']:
            self._write_env(public_key, private_key)
            self.stdout.write(self.style.SUCCESS('Clés VAPID ajoutées au .env local. La clé privée n’a pas été affichée.'))
            return

        self.stdout.write('WEBPUSH_VAPID_PUBLIC_KEY=' + public_key)
        self.stdout.write('WEBPUSH_VAPID_PRIVATE_KEY=' + private_key)
        self.stdout.write(self.style.WARNING(
            'La clé privée est un secret : ne la partagez pas et ne la versionnez pas.'
        ))

    @staticmethod
    def _write_env(public_key, private_key):
        env_path = Path(settings.BASE_DIR) / '.env'
        content = env_path.read_text(encoding='utf-8') if env_path.exists() else ''
        secrets = {
            'WEBPUSH_VAPID_PUBLIC_KEY': public_key,
            'WEBPUSH_VAPID_PRIVATE_KEY': private_key,
        }
        lines = content.splitlines()
        for name in secrets:
            for line in lines:
                if line.startswith(f'{name}=') and line.partition('=')[2].strip():
                    raise CommandError(f'{name} est déjà configurée. Aucune clé n’a été modifiée.')

        values = {**secrets, 'WEBPUSH_ENABLED': 'True'}
        for name, value in values.items():
            matching_line = next((index for index, line in enumerate(lines) if line.startswith(f'{name}=')), None)
            if matching_line is None:
                lines.append(f'{name}={value}')
            else:
                lines[matching_line] = f'{name}={value}'

        env_path.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
