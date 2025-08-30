describe("add nlp task", () => {
  before(() => {
    cy.login();
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


  afterEach(() => {
    cy.task_delete();
  })
  after(() => {
    cy.logout();
  });
});
