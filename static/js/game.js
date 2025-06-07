// Game Interface JavaScript
class GameInterface {
    constructor() {
        this.currencyBalances = {};
        this.initialize();
    }

    initialize() {
        this.bindEvents();
        this.updateCurrencyDisplay();
        this.initializeChoiceValidation();
        this.initializeCustomChoice();
    }

    bindEvents() {
        // Custom choice input handling
        const customChoiceInput = document.getElementById('customChoice');
        if (customChoiceInput) {
            customChoiceInput.addEventListener('input', () => this.validateCustomChoice());
        }

        // Simple form submission - no interference
        const choiceForm = document.getElementById('choiceForm');
        if (choiceForm) {
            // Allow normal form submission without validation interference
            console.log('Choice form found, ready for submission');
        }
    }

    validateChoice(event) {
        const button = event.target;
        const choiceId = button.closest('[data-choice-id]').dataset.choiceId;
        
        // Show loading state
        button.classList.add('loading');
        button.disabled = true;

        // Check if user can afford this choice
        fetch(`/api/currency_check?choice_id=${choiceId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (!data.can_afford) {
                        event.preventDefault();
                        this.showCurrencyError(button, 'Insufficient funds for this choice');
                        return false;
                    }
                    this.currencyBalances = data.currency_balances;
                } else {
                    event.preventDefault();
                    this.showError(data.message || 'Unable to validate choice');
                }
            })
            .catch(error => {
                console.error('Currency check failed:', error);
                event.preventDefault();
                this.showError('Network error. Please try again.');
            })
            .finally(() => {
                button.classList.remove('loading');
                button.disabled = false;
            });
    }

    validateCustomChoice() {
        const customInput = document.getElementById('customChoice');
        const customButton = document.getElementById('customChoiceBtn');
        const errorDiv = document.getElementById('customChoiceError');
        
        if (!customInput || !customButton) return;

        const inputValue = customInput.value.trim();
        const hasText = inputValue.length > 0;
        const hasDiamonds = this.currencyBalances['💎'] >= 1;

        // Enable/disable button based on input and currency
        customButton.disabled = !hasText || !hasDiamonds;

        // Show/hide error message
        if (errorDiv) {
            if (hasText && !hasDiamonds) {
                errorDiv.classList.remove('d-none');
            } else {
                errorDiv.classList.add('d-none');
            }
        }

        // Update button text based on state
        if (hasText && hasDiamonds) {
            customButton.innerHTML = '<i class="fas fa-gem me-2"></i>Execute';
            customButton.classList.remove('btn-secondary');
            customButton.classList.add('btn-warning');
        } else {
            customButton.innerHTML = '<i class="fas fa-gem me-2"></i>Execute';
            customButton.classList.remove('btn-warning');
            customButton.classList.add('btn-secondary');
        }
    }

    initializeChoiceValidation() {
        // Get current currency balances from the page
        const currencyItems = document.querySelectorAll('.currency-item');
        currencyItems.forEach(item => {
            const currency = item.dataset.currency;
            const amount = parseInt(item.textContent.split(' ')[1]);
            this.currencyBalances[currency] = amount;
        });

        // Validate all choices on page load
        document.querySelectorAll('.choice-option').forEach(choice => {
            this.validateChoiceAffordability(choice);
        });
    }

    validateChoiceAffordability(choiceElement) {
        const costBadges = choiceElement.querySelectorAll('.cost-badge:not(.free)');
        const choiceButton = choiceElement.querySelector('.choice-btn');
        let canAfford = true;

        costBadges.forEach(badge => {
            const text = badge.textContent.trim();
            const parts = text.split(' ');
            if (parts.length === 2) {
                const currency = parts[0];
                const amount = parseInt(parts[1]);
                const userAmount = this.currencyBalances[currency] || 0;
                
                if (userAmount < amount) {
                    canAfford = false;
                    badge.classList.add('insufficient-funds');
                }
            }
        });

        if (!canAfford) {
            choiceButton.disabled = true;
            choiceButton.classList.add('insufficient-funds');
            choiceElement.classList.add('unaffordable');
        }
    }

    initializeCustomChoice() {
        // Initialize custom choice validation
        this.validateCustomChoice();
        
        // Character counter for custom choice
        const customInput = document.getElementById('customChoice');
        if (customInput) {
            const maxLength = customInput.getAttribute('maxlength') || 200;
            const counterDiv = document.createElement('div');
            counterDiv.className = 'character-counter text-muted small text-end mt-1';
            customInput.parentNode.appendChild(counterDiv);
            
            const updateCounter = () => {
                const remaining = maxLength - customInput.value.length;
                counterDiv.textContent = `${remaining} characters remaining`;
                
                if (remaining < 20) {
                    counterDiv.classList.add('text-warning');
                } else {
                    counterDiv.classList.remove('text-warning');
                }
            };
            
            customInput.addEventListener('input', updateCounter);
            updateCounter(); // Initial update
        }
    }

    handleFormSubmission(event) {
        // Add loading state to the form
        const form = event.target;
        const submitButton = document.activeElement;
        
        if (submitButton && submitButton.type === 'submit') {
            submitButton.classList.add('loading');
            submitButton.disabled = true;
            
            // Add a timeout to re-enable button if something goes wrong
            setTimeout(() => {
                submitButton.classList.remove('loading');
                submitButton.disabled = false;
            }, 10000);
        }
    }

    showCurrencyError(button, message) {
        // Create or update error tooltip
        let tooltip = button.nextElementSibling;
        if (!tooltip || !tooltip.classList.contains('currency-error')) {
            tooltip = document.createElement('div');
            tooltip.className = 'currency-error text-danger small mt-1';
            button.parentNode.appendChild(tooltip);
        }
        
        tooltip.textContent = message;
        tooltip.style.display = 'block';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            tooltip.style.display = 'none';
        }, 3000);
    }

    showError(message) {
        // Create a toast-like error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        errorDiv.style.cssText = 'top: 80px; right: 20px; z-index: 1050; max-width: 300px;';
        errorDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }

    updateCurrencyDisplay() {
        // Animate currency changes
        const currencyItems = document.querySelectorAll('.currency-item');
        currencyItems.forEach(item => {
            item.addEventListener('transitionend', () => {
                item.classList.remove('currency-change');
            });
        });
    }

    // Utility method to format currency display
    formatCurrency(currency, amount) {
        return `${currency} ${amount.toLocaleString()}`;
    }

    // Method to handle real-time currency updates
    updateCurrencyBalance(currency, newAmount) {
        this.currencyBalances[currency] = newAmount;
        
        const currencyElement = document.querySelector(`[data-currency="${currency}"]`);
        if (currencyElement) {
            currencyElement.textContent = this.formatCurrency(currency, newAmount);
            currencyElement.classList.add('currency-change');
        }
        
        // Re-validate all choices
        this.initializeChoiceValidation();
        this.validateCustomChoice();
    }
}

// Initialize game interface when DOM is loaded
function initializeGameInterface() {
    if (typeof window.gameInterface === 'undefined') {
        window.gameInterface = new GameInterface();
    }
}

// Utility functions for game features
function animateChoiceSelection(choiceElement) {
    choiceElement.classList.add('slide-in-left');
    setTimeout(() => {
        choiceElement.classList.remove('slide-in-left');
    }, 500);
}

function showTypingEffect(element, text, speed = 50) {
    element.textContent = '';
    let i = 0;
    
    const typeWriter = () => {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(typeWriter, speed);
        }
    };
    
    typeWriter();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { GameInterface, initializeGameInterface };
}
