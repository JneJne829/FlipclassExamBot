(function(answerInput, targetScore) {
    console.log("接收到的答案字符串：", answerInput);
    console.log("目標分數：", targetScore);

    const answers = {};
    answerInput.trim().split('\n').forEach(line => {
        const [id, answerPart] = line.split(' - ');
        if (id && answerPart) {
            const answerValues = answerPart.split(',').map(ans => ans.trim());
            answers[id.trim()] = answerValues;
        }
    });

    console.log("解析後的答案對象：", answers);
    
    const questions = Array.from(document.querySelectorAll('.kques-item[data-parentid=""]'));
    const totalQuestions = questions.length;

    if (isNaN(targetScore) || targetScore < 0 || targetScore > 100) {
        alert("目標分數無效，必須是 0 到 100 之間的整數。");
        return;
    }

    const pointsPerQuestion = 100 / totalQuestions;
    console.log("每題分數：", pointsPerQuestion);

    const targetPoints = targetScore;
    const correctQuestionsNeeded = Math.floor(targetPoints / pointsPerQuestion);
    const remainingPoints = targetPoints % pointsPerQuestion;

    console.log("需要答對題數：", correctQuestionsNeeded);
    console.log("剩餘分數：", remainingPoints);

    const questionIds = questions.map(question => question.getAttribute('data-id'));
    
    const correctQuestionIds = questionIds.slice(0, correctQuestionsNeeded);
    const wrongQuestionIds = questionIds.slice(correctQuestionsNeeded);

    console.log("答對題目ID：", correctQuestionIds);
    console.log("答錯題目ID：", wrongQuestionIds);

    questions.forEach(question => {
        const dataId = question.getAttribute('data-id');
        const correctAnswer = answers[dataId];

        if (correctAnswer) {
            const questionType = question.getAttribute('type');
            const shouldAnswerWrong = wrongQuestionIds.includes(dataId);

            if (questionType === '0') {
                const inputs = Array.from(question.querySelectorAll('input[type="radio"]'));
                
                if (shouldAnswerWrong) {
                    const wrongInputs = inputs.filter((input, index) => {
                        const optionSpan = input.nextElementSibling;
                        return optionSpan && !correctAnswer.includes(optionSpan.textContent.trim());
                    });
                    if (wrongInputs.length > 0) {
                        wrongInputs[0].checked = true;
                    } else {
                        inputs.forEach(input => input.checked = false);
                    }
                } else {
                    inputs.forEach((input, index) => {
                        const optionSpan = input.nextElementSibling;
                        if (optionSpan) {
                            input.checked = correctAnswer.includes(optionSpan.textContent.trim());
                        }
                    });
                }
            } else if (questionType === '1') {
                const inputs = Array.from(question.querySelectorAll('input[type="checkbox"], input[type="radio"]'));

                if (shouldAnswerWrong) {
                    const wrongInputs = inputs.filter(input => {
                        const optionText = input.closest('label').textContent.trim().replace(/^[A-Z]\.\s*/, '');
                        return !correctAnswer.map(ans => ans.toLowerCase()).includes(optionText.toLowerCase());
                    });
                    if (wrongInputs.length > 0) {
                        wrongInputs[0].checked = true;
                    } else {
                        inputs.forEach(input => input.checked = false);
                    }
                } else {
                    inputs.forEach(input => {
                        const optionText = input.closest('label').textContent.trim().replace(/^[A-Z]\.\s*/, '');
                        input.checked = correctAnswer.map(ans => ans.toLowerCase()).includes(optionText.toLowerCase());
                    });
                }
            } else if (questionType === '2') {
                const inputs = question.querySelectorAll('.gap-input, input[type="text"], textarea');
                
                if (shouldAnswerWrong) {
                    inputs.forEach(input => {
                        input.value = " ";
                    });
                } else {
                    const processedAnswers = correctAnswer.flatMap(ans => {
                        const parts = ans.split('、');
                        return parts.map(part => {
                            // 處理數字範圍 1.5--3
                            const numericRangeMatch = part.match(/([\d.]+)--([\d.]+)/);
                            if (numericRangeMatch) {
                                return numericRangeMatch[1];
                            }
                            
                            // 處理字母範圍 A--C
                            const letterRangeMatch = part.match(/([A-Za-z])--([A-Za-z])/);
                            if (letterRangeMatch) {
                                return letterRangeMatch[1];
                            }
                            
                            // 處理一般包含|的答案
                            if (part.includes('|')) {
                                return part.split('|')[0].trim();
                            }
                            
                            return part.trim();
                        });
                    });
                    
                    processedAnswers.forEach((ans, idx) => {
                        if (inputs[idx]) {
                            inputs[idx].value = ans;
                        }
                    });
                }
            }
        }
    });

    const expectedScore = (correctQuestionsNeeded * pointsPerQuestion);
    console.log("預期分數：", expectedScore);
    console.log("所有答案已成功填充！");

})(arguments[0], arguments[1]);