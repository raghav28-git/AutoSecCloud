const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get('/', (req, res) => {
    res.json({
        status: "healthy",
        service: "Clean Node Microservice",
        timestamp: new Date().toISOString()
    });
});

app.get('/health', (req, res) => {
    res.json({ status: "UP" });
});

if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`Clean service listening on port ${PORT}`);
    });
}
