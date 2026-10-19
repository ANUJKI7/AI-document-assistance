// Question history kept in this browser (the backend does not store it)
const HISTORY_KEY = "questionHistory";

function getQuestionHistory() {
    try {
        return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    } catch (error) {
        return [];
    }
}

function addQuestionToHistory(question, answered) {
    const history = getQuestionHistory();
    history.unshift({
        question: question,
        answered: answered,
        asked_at: new Date().toISOString()
    });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 50)));
}
