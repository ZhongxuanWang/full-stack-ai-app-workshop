# CDS Datathon Spring 2025, Workshop on AI Integrated Full Stack Web App

## [Workshop Presentation](https://docs.google.com/presentation/d/1E23JgsLinDPs51u1VnHnFIWNKWmDsohXFly82qdXltI/edit?usp=sharing)

## Frontend Set up

1. Run `npx create-next-app@latest frontend`<br>
2. **No** typescript (keep it simpler)<br>
3. **Yes** ESLint (ESLint is a tool that analyzes your JavaScript (or TypeScript) code to find and fix problems.)<br>
4. **No** Tailwind CSS (we will use our own global CSS for simplicity)<br>
5. **No** `src/` directory (we will use our own `app` directory)<br>
6. **Yes** App Router (App Router is a new way to build applications in Next.js. It allows you to define your application structure using folders and files, making it easier to manage and understand your codebase.)<br>
7. **No** Turbopack (Turbopack is a new Rust-based bundler for JavaScript and TypeScript applications. It is designed to be faster than Webpack, but it is still in alpha and not recommended for production use.)<br>
8. **No** customize adefault import alias (we will use our own import alias)<br>

Note: In the frontend folder, we are only modifying the globals.css and page.js

## Backend Set up
1. Get your OpenAI API key from https://platform.openai.com/signup
2. Create a new file called `.env` in the backend folder and add your OpenAI API key to it, so it will look like something like this
```bash
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```
Other items are not reiterated here. Please refer to the workshop for more information :)


## Spin up the application
Assuming you have already configured everything properly according to the workshop, then you should do 

1. Spin up the backend server
```bash
cd backend
uvicorn main:app --reload --port 8000
```

2. Spin up the frontend server
```bash
npm run dev
```

3. Open your browser and go to `http://localhost:3000` to see the frontend application running.