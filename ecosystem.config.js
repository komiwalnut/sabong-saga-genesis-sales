module.exports = {
    apps: [
      {
        name: "ssg-sales-tracker",
        script: "./main.py",
        interpreter: "./sabungan-venv/bin/python3",
        watch: false,
        autorestart: true
      }
    ]
  };
  