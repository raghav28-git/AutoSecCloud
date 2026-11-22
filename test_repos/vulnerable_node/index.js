// Vulnerable Node.js Sample Application
const child_process = require('child_process');

const JWT_SECRET = "super_secret_jwt_key_123456789_exposed"; // HARDCODED SECRET - HIGH

function handleUserRequest(req) {
    const code = req.query.code;
    // DANGEROUS EVAL CALL - CRITICAL
    eval(code);

    // DANGEROUS EXEC CALL - HIGH
    child_process.exec("ls " + req.query.dir);
}

console.log("Vulnerable Node server starting...");
