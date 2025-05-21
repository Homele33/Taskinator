// cypress/e2e/api-interactions.cy.ts

describe('Task API Interactions', () => {
  beforeEach(() => {
    // Visit the app and log in
    cy.visit('/login');
    // Stub the response for fetching tasks
    cy.intercept('GET', '/api/tasks', {
      statusCode: 200,
      body: [
        {
          id: 1,
          title: 'Stubbed Task 1',
          description: 'This is a stubbed task',
          status: 'TODO',
          priority: 'HIGH',
          subtasks: []
        }
      ]
    }).as('getTasks');
  });

  it('should display stubbed tasks from the API', () => {
    // Wait for the API call to complete
    cy.wait('@getTasks');

    // Verify the stubbed task is displayed
    cy.get('[data-testid="task-list"]').contains('Stubbed Task 1').should('be.visible');
  });

  it('should send the correct data when creating a task', () => {
    // Stub the POST request
    cy.intercept('POST', '/api/tasks', {
      statusCode: 201,
      body: {
        id: 2,
        title: 'New Task',
        status: 'TODO',
        priority: 'MEDIUM'
      }
    }).as('createTask');

    // Create a new task
    cy.get('[data-testid="add-task-button"]').click();
    cy.get('[data-testid="task-title-input"]').type('New Task');
    cy.get('[data-testid="task-priority-select"]').select('MEDIUM');
    cy.get('[data-testid="submit-task-button"]').click();

    // Verify the POST request was made with the correct data
    cy.wait('@createTask').its('request.body').should('deep.include', {
      title: 'New Task',
      priority: 'MEDIUM'
    });
  });
});
