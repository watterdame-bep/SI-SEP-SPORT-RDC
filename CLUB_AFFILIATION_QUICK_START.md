# Club Affiliation Interface - Quick Start Guide

## Access the Interface

### For Ligue Secretaries:
1. Log in to the system
2. Go to the sidebar menu under "Gestion Ligue"
3. Click on **"Affiliation de Clubs"** to access the club management interface

### Direct URLs:
- **Club Affiliation Dashboard**: `/gouvernance/ligue/clubs/affiliation/`
- **Create Club - Step 1**: `/gouvernance/ligue/clubs/create/step1/`
- **Create Club - Step 2**: `/gouvernance/ligue/clubs/create/step2/`
- **Create Club - Step 3**: `/gouvernance/ligue/clubs/create/step3/`
- **Club Details**: `/gouvernance/ligue/clubs/<club_id>/`

## Creating a Club

### Step 1: Club Identity
Fill in the following information:
- **Nom officiel** (Required): Official name of the club
- **Sigle** (Required): Club abbreviation/acronym
- **Code unique** (Required): Unique identifier for the club
- **Statut juridique** (Optional): Legal status (e.g., "Association sans but lucratif")
- **Email officiel** (Optional): Official email address
- **Téléphone officiel** (Optional): Official phone number

### Step 2: Address & Localization
- **Avenue/Rue** (Required): Street address
- **Commune** (Optional): City/commune name

### Step 3: Sports Disciplines
- **Disciplines** (Required): Select at least one sport discipline
  - Checkboxes for all active disciplines in the system
  - Multiple selections allowed

### Submission
- Click "Créer le Club" to finalize
- System will create the club and link it to your ligue
- Success message will confirm creation
- You'll be redirected to the club affiliation dashboard

## Club Affiliation Dashboard

### Features:
1. **Statistics Cards**
   - Total affiliated clubs
   - Disciplines covered by the ligue
   - League information (sigle)

2. **Club List Table**
   - Club name and code
   - Club sigle (badge)
   - Associated disciplines
   - Activation status
   - View button for details

3. **Create Club Button**
   - Located in the top-right corner
   - Yellow button with "+" icon
   - Starts the multi-step creation process

### Empty State
- If no clubs exist, you'll see a helpful message
- Direct link to create your first club

## Club Details View

Access by clicking "Voir" (View) on any club in the list:
- View complete club information
- See affiliated disciplines
- View contact details
- See address information

## Data Structure

### Club Creation Flow:
```
Ligue Secretary
    ↓
Affiliation Dashboard
    ↓
Create Club (Step 1: Identity)
    ↓
Create Club (Step 2: Address)
    ↓
Create Club (Step 3: Disciplines)
    ↓
Club Created & Linked to Ligue
    ↓
Back to Affiliation Dashboard
```

### Club Hierarchy:
```
Fédération Nationale
    └── Ligue Provinciale
        └── Club (Affiliated)
            ├── Disciplines
            ├── Address
            └── Contact Info
```

## Important Notes

1. **Session Management**
   - Form data is stored in session between steps
   - If you leave the form, you'll need to start over
   - Session data is cleared after successful creation

2. **Club Status**
   - Newly created clubs are automatically set to "ACTIVE"
   - Clubs inherit the ligue's province_admin

3. **Disciplines**
   - Clubs can have multiple disciplines
   - Only active disciplines are available for selection
   - Disciplines are managed in the system parameters

4. **Validation**
   - All required fields must be filled
   - Form validates at each step
   - Error messages guide you to fix issues

## Troubleshooting

### "Profil utilisateur introuvable"
- Ensure you're logged in as a ligue secretary
- Check that your user profile is properly configured

### "Vous n'êtes pas associé à une ligue provinciale"
- Verify your account is linked to a ligue
- Contact your administrator if needed

### "Veuillez d'abord compléter l'étape 1"
- You're trying to access step 2 without completing step 1
- Go back and complete the previous step

### Form validation errors
- Check that all required fields (marked with *) are filled
- Ensure email format is valid if provided
- Select at least one discipline in step 3

## Tips & Best Practices

1. **Club Naming**
   - Use clear, official names
   - Include location if helpful (e.g., "Club Sportif de Kinshasa")

2. **Club Codes**
   - Use consistent naming convention
   - Example: CLUB-001, CLUB-002, etc.

3. **Disciplines**
   - Select all disciplines the club practices
   - This helps with reporting and statistics

4. **Contact Information**
   - Keep email and phone updated
   - Use official contact details

## Related Features

- **Mes Clubs Affiliés**: View all clubs in a simple list
- **Documents Officiels**: Access ligue documents
- **Mon Profil**: Manage ligue signature and seal
- **Tableau de Bord**: View ligue statistics and alerts

## Support

For issues or questions:
1. Check this guide first
2. Review error messages carefully
3. Contact your system administrator
4. Check the system logs for detailed error information
