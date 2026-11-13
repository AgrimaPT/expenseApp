# ExpenseApp – Multi-Branch Restaurant Management System

ExpenseApp is a multi-branch restaurant financial management application built with Django. It enables restaurant owners to monitor income, expenses and profitability across multiple branches, while managers, partners and staff manage branch-level financial activities through role-based access control.

## Features

### Owner Dashboard
- Access and monitor multiple restaurant branches from a single account.
- View daily income, expenses and profit across all branches.
- Monitor monthly financial performance.
- Track the financial performance of individual branches.

### Manager Dashboard
- Access and manage the assigned branch.
- Review and verify daily income records.
- Verify purchases and expenses.
- Monitor branch-level financial activities.

### Partner Dashboard
- Access financial information only for the branch they are partnered with.
- View branch-specific income, expenses and financial performance.
- Restricted from accessing other branches' financial records.

### Staff Dashboard
- Record daily purchases and expenses.
- Update financial transactions for the assigned branch.

## User Roles & Access Control

The application implements four role-based access levels:

| Role | Access & Permissions |
|---|---|
| **Owner** | Full access to all branches and consolidated financial performance. |
| **Manager** | Branch-level access to review and verify income, purchases and expenses. |
| **Partner** | Read-only access to financial details of their associated branch. |
| **Staff** | Access to record daily purchases and expenses for the assigned branch. |

## Financial Management
- Maintain daily income and expense records.
- Calculate daily branch-level profit.
- Track monthly financial performance.
- Organise financial data by restaurant branch.
- Centralise financial monitoring across multiple branches.

## Application Workflow

1. **Staff** record daily purchases and expenses for their assigned branch.
2. **Managers** review and verify branch-level income and purchase records.
3. The application maintains daily income, expenses and profit calculations.
4. **Partners** view financial information restricted to their associated branch.
5. **Owners** monitor all branches through a centralised dashboard and review daily and monthly financial performance.

## Technology Stack

- **Backend:** Python, Django
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **Database:** SQLite
- **Deployment:** AWS EC2, Linux, Gunicorn, Nginx, SSL/HTTPS

## Author

**Agrima P T**

- GitHub: [AgrimaPT](https://github.com/AgrimaPT)
- LinkedIn: [Agrima](https://www.linkedin.com/in/contactagrima/)
