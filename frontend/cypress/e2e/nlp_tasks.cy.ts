describe("add nlp task", () => {
  before(() => {
    cy.login("test@example.com", "password123");
  });

  it("should create new task", () => {
    // input task text into nlp-input
    cy.get('[data-testid="nlp-input"]').type("testing nlp today at 13:00");
    cy.get('[data-testid="nlp-submit"]').click(); // submit task
    // make sure task is visiable
    cy.get('[data-testid="task-list"]').should("be.visible");

    // check the task for the right information
    cy.get('[data-testid^="task-title"]').should("contain.text", "Test");
    cy.get('[data-testid^="task-status"]').should("contain.text", "Todo");
    cy.get('[data-testid^="task-"]').should("contain.text", "1:00:00 PM");
  });

  it("should add subtask", () => {
    // add subtask to task
    cy.task_reload();
    cy.intercept("GET", "api/tasks/subtasks/*").as("subtasks");
    cy.get('[data-testid^="task-menu"]').first().click();
    cy.get('[data-testid^="task-add-subtask"]').first().click();
    cy.get('[data-testid="subtask-input"]').type("testing subtask");
    cy.get('[data-testid="subtask-submit"]').click(); // submit subtask
    // make sure subtask is visiable
    cy.wait("@subtasks")
    cy.get('[data-testid^="subtask-list"]').should("be.visible");
    // check the subtask for the right information
    cy.get('[data-testid^="subtask-title"]').should(
      "contain.text",
      "testing subtask"
    );
  });

  it("should delete task", () => {
    // delete task from task-list
    cy.task_delete();

    cy.reload;
    cy.get('[data-testid^="task-list"]').should("be.visible");
  });
  after(() => {
    cy.logout();
  });
});
