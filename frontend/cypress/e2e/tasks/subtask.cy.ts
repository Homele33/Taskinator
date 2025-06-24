describe("test subtasks", () => {
  before(() => {
    cy.login();
  });

  it("should add subtask", () => {
    // add subtask to task
    cy.get('[data-testid="nlp-input"]').type("testing subtasks today at 13:00");
    cy.get('[data-testid="nlp-submit"]').click(); // submit task

    cy.task_reload();

    cy.intercept("GET", "api/tasks/subtasks/*").as("subtasks");
    cy.get('[data-testid^="task-menu"]').first().click();
    cy.get('[data-testid^="task-add-subtask"]').first().click();
    cy.get('[data-testid="subtask-input"]').type("testing subtask");
    cy.get('[data-testid="subtask-submit"]').click(); // submit subtask
    // make sure subtask is visiable
    cy.wait("@subtasks")

    cy.task_reload();
    cy.get('[data-testid^="task-subtasks-toggle"]').first().click();

    cy.get('[data-testid^="subtask-list"]').should("be.visible");
    // check the subtask for the right information
    cy.get('[data-testid^="subtask-title"]').should(
      "contain.text",
      "testing subtask"
    );
  });

  it("should edit subtasks", () => {
    cy.task_reload();
    cy.get('[data-testid^="task-subtasks-toggle"]').first().click();

    cy.get('[data-testid^="subtask-menu"]').first().click();

    cy.get('[data-testid^="subtask-edit-button"]').first().click();

    cy.get('[data-testid="subtask-input"]').clear().type("edit subtask")

    cy.get('[data-testid="subtask-submit"]').click();

    cy.task_reload();

    cy.get('[data-testid^="task-subtasks-toggle"]').first().click();

    cy.get('[data-testid^="subtask-title"]').should(
      "contain.text",
      "edit subtask"
    );
  })

  it("should toggle subtask completion", () => {
    cy.task_reload();

    cy.intercept("GET", "api/tasks/subtasks/*").as("subtasks");

    cy.get('[data-testid^="task-subtasks-toggle"]').first().click();

    cy.wait("@subtasks")
    cy.get('[data-testid^="subtask-complete-toggle"]').first().click();

    cy.get('[data-testid^="subtask-card"]').should("have.class", "bg-success")

    cy.get('[data-testid^="subtask-complete-toggle"]').first().click();

    cy.get('[data-testid^="subtask-card"]').should("not.have.class", "bg-success")
  })

  it("should delete subtask", () => {
    cy.task_reload();

    cy.get('[data-testid^="task-subtasks-toggle"]').first().click();

    cy.get('[data-testid^="subtask-menu"]').first().click();
    cy.get('[data-testid^="subtask-delete-button"]').first().click();
  })

  after(() => {
    cy.task_delete();
    cy.logout();
  });
})
