# Contoso returns and refunds

Contoso Gear accepts unused products with original packaging within 60 calendar
days of delivery. This is a Contoso policy, not Northwind's 30-day policy. Contact
Contoso support for a return authorization before shipping the product. Authorized
Contoso change-of-mind return postage is free.

## Processing

Contoso inspects returned goods within 5 business days of arrival and then processes
an approved refund to the original payment method. Bank posting may take another
3 to 5 business days. Personalization and clearance products are excluded from
change-of-mind returns. Damaged items use Contoso's separate review procedure.

## Tenant boundary

This article belongs only to Contoso. A Northwind search must not return it even if
it is a closer semantic match for a question about a 60-day return window. The shared
article id is intentional: tenant identity must remain part of every storage key,
join and retrieval filter.
