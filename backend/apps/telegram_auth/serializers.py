from rest_framework import serializers


class TelegramLoginSerializer(serializers.Serializer):
    init_data = serializers.CharField()


class BotLoginSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    username = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)


class RegisterPhoneSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=32)

    def validate_phone_number(self, value: str) -> str:
        raw = value.strip().replace(" ", "").replace("-", "")
        if raw.startswith("0"):
            raw = f"+251{raw[1:]}"
        if not raw.startswith("+"):
            raw = f"+{raw}"
        if not raw[1:].isdigit():
            raise serializers.ValidationError("Phone number must contain only digits.")
        if len(raw) < 10 or len(raw) > 16:
            raise serializers.ValidationError("Invalid phone number format.")
        return raw
