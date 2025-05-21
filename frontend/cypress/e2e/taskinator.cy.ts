describe('Task Management App', () => {
  beforeEach(() => {
    // Visit the main app page before each test
    cy.visit('/');

    // Refresh to apply the mock login
    cy.visit('/');
  });

  it('should display the task list', () => {
    cy.get('[data-testid="task-list"]').should('be.visible');
  });

  it('should open the create task form', () => {
    cy.get('[data-testid="add-task-button"]').click();
    cy.get('[data-testid="create-task-form"]').should('be.visible');
  });

  it('should create a new task', () => {
    const taskTitle = 'Test Task ' + Date.now();

    // Open the form
    cy.get('[data-testid="add-task-button"]').click();

    // Fill out the form
    cy.get('[data-testid="task-title-input"]').type(taskTitle);
    cy.get('[data-testid="task-description-input"]').type('This is a test task description');
    cy.get('[data-testid="task-priority-select"]').select('MEDIUM');
    cy.get('[data-testid="task-status-select"]').select('TODO');

    // Submit the form
    cy.get('[data-testid="submit-task-button"]').click();

    // Verify the task was created
    cy.get('[data-testid="task-list"]').contains(taskTitle).should('be.visible');
  });

  it('should add a subtask to an existing task', () => {
    // First create a task if needed
    // Then open the task details
    cy.get('[data-testid="task-item"]').first().click();

    // Add a subtask
    cy.get('[data-testid="add-subtask-button"]').click();
    cy.get('[data-testid="subtask-title-input"]').type('Test Subtask');
    cy.get('[data-testid="submit-subtask-button"]').click();

    // Verify the subtask was added
    cy.get('[data-testid="subtask-list"]').contains('Test Subtask').should('be.visible');
  });

  it('should mark a task as completed', () => {
    // Find the first task and click its checkbox or complete button
    cy.get('[data-testid="task-item"]').first().within(() => {
      cy.get('[data-testid="task-status-select"]').select('COMPLETED');
    });

    // Verify the task status changed
    cy.get('[data-testid="task-item"]').first().should('have.class', 'completed');
  });

  it('should filter tasks by status', () => {
    // Click on the filter dropdown
    cy.get('[data-testid="filter-status-select"]').select('IN_PROGRESS');

    // Verify only in-progress tasks are shown
    cy.get('[data-testid="task-item"]').each(($el) => {
      cy.wrap($el).should('contain', 'IN_PROGRESS');
    });
  });

  it('should filter tasks by priority', () => {
    // Click on the priority filter
    cy.get('[data-testid="filter-priority-select"]').select('HIGH');

    // Verify only high priority tasks are shown
    cy.get('[data-testid="task-item"]').each(($el) => {
      cy.wrap($el).should('contain', 'HIGH');
    });
  });
});
