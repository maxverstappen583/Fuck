# Use Python 3.11 slim (includes audioop and full standard library)
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy all files (bot.py, requirements.txt, .env, etc.) into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port (for keep-alive)
EXPOSE 8080

# Start the bot
CMD ["python", "bot.py"]
