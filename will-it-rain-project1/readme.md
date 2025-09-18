<!-- Before touching the project, make sure your system has: -->
<!-- ******************* -->
Node.js → Download
 (version 16 or higher)
<!-- ******************* -->
Python → Download
 (version 3.9 or higher)
<!-- ******************* -->
<!-- Yarn (package manager for frontend) -->

<!-- 🔹 On Windows
Open Command Prompt (CMD) or PowerShell (not VS Code terminal yet).
Run: -->
npm install -g yarn
<!-- Verify installation: -->
yarn -v

<!-- 🔹 On Mac/Linux
Open Terminal.
Run: -->
npm install -g yarn
<!-- Verify: -->
yarn -v

<!-- 2️⃣ Project Folder Setup -->

<!-- Open VS Code → Open Terminal → Create a project folder: -->
mkdir will-it-rain-project
cd will-it-rain-project
<!-- Your project will look like this later: -->
will-it-rain-project/
├── backend/     ← Python (FastAPI)
├── frontend/    ← React (UI)
└── README.md

<!-- 3️⃣ Backend (FastAPI + Python) Setup
Step A: Create backend folder -->
mkdir backend
cd backend
<!-- Step B: Virtual Environment
This keeps Python libraries isolated.
Windows: -->
python -m venv venv
venv\Scripts\activate

<!-- Mac/Linux: -->
python3 -m venv venv
source venv/bin/activate

<!-- ✅ Once activated, you’ll see (venv) in your terminal. -->

