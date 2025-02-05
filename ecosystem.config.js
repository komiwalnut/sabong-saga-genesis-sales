module.exports = {
    apps: [
      {
        name: "sabong-saga-genesis-sales-tracker",
        script: "./main.py",
        interpreter: "./sabungan-venv/bin/python3",
        watch: false,
        autorestart: true
      }
    ]
  };
  