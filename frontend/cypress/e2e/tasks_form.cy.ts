describe("test task form", () => {
  before(() => {
    cy.login("test@example.com", "password123");
  });

  it("should create a task with title and description and default values using task form", () => {
    // open new task form
    cy.get('[data-testid="new-task-button"]').click();

    // title
    const title = "Test Task title"
    cy.get('[data-testid="task-title-input"]').type(title);
    // description
    const description = "Test Task with title and description else default values"
    cy.get('[data-testid="task-description-input"]').type(description);
    // submit
    cy.get('[data-testid="save-task-button"]').click();


    cy.task_reload();
    // check task details
    cy.get('[data-testid^="task-title"]').should("contain.text", title);

    cy.get('[data-testid^="task-description"]').should("contain.text", description);

    cy.get('[data-testid^="task-status"]').should("contain.value", "TODO");

  })

  it("should create a task with no default values using task form ", () => {
    // open new task form
    cy.task_reload();
    cy.get('[data-testid="new-task-button"]').click();

    const title = "Test task form with all fields"
    const description = "Test description"
    const date = "2025-07-23T10:00"
    const formatDate = new Date(date).toLocaleString();

    //title
    cy.get('[data-testid="task-title-input"]').type(title);
    // type
    cy.get('[data-testid="task-type-select"]').select(2);
    // description
    cy.get('[data-testid="task-description-input"]').type(description);
    // status
    cy.get('[data-testid="task-status-select"]').select(1);
    // priority
    cy.get('[data-testid="task-priority-select"]').select(0);
    // date and time
    cy.get('[data-testid="task-datetime-input"]').type(date);

    // submit
    cy.get('[data-testid="save-task-button"]').click();

    cy.task_reload();
    // check task values  

    cy.get('[data-testid^="task-title"]').should("contain.text", title);
    cy.get('[data-testid^="task-description"]').should("contain.text", description);
    cy.get('[data-testid^="task-status"]').should("not.contain.value", "TODO");

    cy.get('[data-testid^="task-priority"]').should("not.contain.text", "MEDIUM");
    cy.get('[data-testid^="task-datetime"]').should("contain.text", formatDate);
    cy.get('[data-testid^="task-type"]').should("not.contain.text", "Meeting");
  });

  after(() => {
    cy.logout();
  })

  afterEach(() => {
    cy.task_delete()
  })
})
