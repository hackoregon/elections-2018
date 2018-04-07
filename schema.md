# Proposed Schema

## Committee History
* **committee_id** int foreign
    - foreign key (to committeeslist org stmt)
* **committee_name** varchar(255)
* **committee_description** varchar(255)
* **effecitve** date
* **expiration** date
* **file_type** varchar(32)

## Committees List
* **id** int primary
* **filer_name** varchar(255)
* **filer_description** varchar(255)

## Election Activity
(primary key will be sequence)
* **election** varchar(32)
* **committee_id** int
    - foreign key (to committeeslist org stmt)
* **active_date** date
* **status** varchar(8)
* **active_reason** varchar(255)

## Statement of Organization
* **committee_id** int primary
* **committee_name** varchar(255)
    - unique
* **candidate_address** varchar(255)
* **committee_acronym** varchar(32)
* **committee_address** varchar(255)
* **committee_campaign_phone** varchar(16)
* **committee_filing_effective_from** varchar(255)
* **committee_filing_type** varchar(10)
* **committee_pac_type** varchar(32)
* **election_office** varchar(255)
* **email_address** varchar(255)
* **employer** varchar(255)
* **fax** varchar(16)
* **home_phone** varchar(16)
* **mailing_address** varchar(255)
* **name** varchar(255)
* **occupation** varchar(255)
* **party_affiliation** varchar(11)
* **treasurer_email_address** varchar(255)
* **treasurer_fax** varchar(16)
* **treasurer_home_phone** varchar(16)
* **treasurer_mailing_address** varchar(255)
* **treasurer_name** varchar(255)
* **treasurer_work_phone** varchar(16)
* **work_phone** varchar(16)

## Transaction
* **transaction_id** int primary
* **committee_id** int
    - foreign key (to committeeslist org stmt)
* **transaction_date** date
* **status** varchar(32)
* **filer_committee** varchar(255)
* **contributor_payee** varchar(255)
* **transaction_subtype** varchar(255)
* **amount** numeric

## Transaction Details
* **transaction_id** int primary
    - this will join with primary in Transaction
* **payee_id** foreign
    - to Payee table
* **donor_id** foreign
    - to Donor table
* **address** varchar(255)
* **address_book_type** varchar(32)
* **agent** varchar(32)
* **aggregate** numeric
* **amount** numeric
* **associations** varchar(255)
* **check** int
* **description** varchar(255)
* **due_date** timestamp
* **employer_name** varchar(255)
* **exam_letter_date** date
* **filed_date** timestamp
* **inkind_independent_expenditures** varchar(255)
* **interest_rate** varchar(255)
* **name** varchar(255)
* **occupation** varchar(255)
* **occupation_letter_date** date
* **payer_of_personal_expenditure** varchar(255)
* **payment_method** varchar(32)
* **process_status** varchar(32)
* **purpose** varchar(255)
* **repayment_schedule** varchar(32)
* **transaction_date** date
* **transaction_sub_type** varchar(255)
* **transaction_type** varchar(32)

## Donor
* **donor_id** int primary
* **donor_name** varchar(255)
* **donor_address** varchar(255)
* **donor_type** varchar(32)
* **donor_cats** jsonb

## Payee
* **payee_id** int primary
* **payee_name** varchar(255)

## ballots
* **json** jsonb