describe("test task edit", () => {
  before(() => {
    cy.login();
  });


  it("should create a task then edit the task", () => {
    cy.get('[data-testid="new-task-button"]').click();

    // define initial values

    let title = "Test task edit"
    let description = "Test description"
    let date = "2025-07-23T10:00"
    const d = new Date(date);
    let formatDate = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;

    //title
    cy.get('[data-testid="task-title-input"]').type(title);
    // description
    cy.get('[data-testid="task-description-input"]').type(description);

    // submit
    cy.get('[data-testid="save-task-button"]').click();

    cy.task_reload();

    // check initial values
    cy.get('[data-testid^="task-title"]').should("contain.text", title);
    cy.get('[data-testid^="task-description"]').should("contain.text", description);

    // change values
    title = "Test Edit";
    description = "Edit testing";

    // edit the task

    cy.get('[data-testid^="task-menu"]').first().click();
    cy.get('[data-testid^="task-edit-button"]').first().click();

    //title
    cy.get('[data-testid="task-title-input"]').clear().type(title);
    // description
    cy.get('[data-testid="task-description-input"]').clear().type(description);
    // type
    cy.get('[data-testid="task-type-select"]').select(2);
    // status
    cy.get('[data-testid="task-status-select"]').select(1);
    // priority
    cy.get('[data-testid="task-priority-select"]').select(2);
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

    cy.get('[data-testid^="task-status-"]').select(0);
    cy.get('[data-testid^="task-status"]').should("contain.value", "TODO");
  });

  after(() => {
    cy.task_delete();
    cy.logout();
  })
})
